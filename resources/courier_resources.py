from flask import request, make_response, jsonify, abort
from flask_restful import Resource
from data.couriers import Courier
from data.couriers_type import CourierType
from data.db_session import create_session
from data.intervals import Interval
from data.intervals_delivery import IntervalDelivery
from data.orders import Order
from data.orders_regions import OrderRegion
from data.regions import Regions


class CouriersListResource(Resource):
    def post(self):
        sess = create_session()
        keys = ['courier_id', 'courier_type', 'regions', 'working_hours']
        not_validate_couriers = []
        validate_object = []
        for courier_data in request.get_json()['data']:
            if not all(key in keys for key in courier_data) or len(keys) != len(courier_data):
                not_validate_couriers.append(courier_data['courier_id'])
                continue
            if not isinstance(courier_data['regions'], list) or not isinstance(courier_data['working_hours'], list):
                not_validate_couriers.append(courier_data['courier_id'])
                continue

            try:
                courier = Courier(courier_id=courier_data['courier_id'], courier_type=courier_data['courier_type'])
                regions = [Regions(courier_id=courier_data['courier_id'], region=region) for region in
                           courier_data['regions']]
                intervals = [Interval(courier_id=courier_data['courier_id'],
                                      time_start=time, time_stop=time) for time in courier_data['working_hours']]
                validate_object.extend([courier] + regions + intervals)
            except (ValueError, AssertionError, TypeError, IndexError):
                not_validate_couriers.append(courier_data['courier_id'])

        if not_validate_couriers:
            return make_response(
                jsonify(
                    {'validation_error': {'couriers': [{'id': courier_id} for courier_id in not_validate_couriers]}}),
                400)
        for new_object in validate_object:
            sess.add(new_object)
        sess.commit()
        return make_response(jsonify({'couriers': [{'id': courier.courier_id} for courier in
                                                   filter(lambda x: isinstance(x, Courier), validate_object)]}), 201)


class CouriersResource(Resource):
    def patch(self, courier_id):
        try:
            courier_id = int(courier_id)
        except ValueError:
            abort(400)

        sess = create_session()
        delete_objects = []
        add_objects = []
        keys = ['courier_type', 'regions', 'working_hours']
        data: dict = request.get_json()

        if not any([key in data for key in keys]) or (set(data.keys()) - set(keys)):
            abort(400)
        if courier_id not in [courier.courier_id for courier in sess.query(Courier).all()]:
            abort(400)

        keys = list(set(keys) & set(data.keys()))
        courier = sess.query(Courier).filter(Courier.courier_id == courier_id).first()
        try:
            if 'regions' in keys:
                if not isinstance(data['regions'], list) or len(data['regions']) == 0:
                    abort(400)
                delete_objects.extend(sess.query(Regions).filter(Regions.courier_id == courier_id).all())
                add_objects.extend([Regions(courier_id=courier_id, region=region) for region in data['regions']])
            if 'working_hours' in keys:
                if not isinstance(data['working_hours'], list):
                    abort(400)
                delete_objects.extend(sess.query(Interval).filter(Interval.courier_id == courier_id).all())
                add_objects.extend([Interval(courier_id=courier_id, time_start=time, time_stop=time) for time in
                                    data['working_hours']])
            if 'courier_type' in keys:
                courier.courier_type = data['courier_type']
        except (ValueError, AssertionError, IndexError, TypeError):
            abort(400)

        for delete_object in delete_objects:
            sess.delete(delete_object)
        for add_object in add_objects:
            sess.add(add_object)
        sess.commit()

        delivery = sess.query(Order).filter(Order.courier_id == courier_id, Order.complete_time == None).all()
        delivery = sorted(delivery, key=lambda x: x.weight, reverse=True)
        courier_regions = [region.region for region in
                           sess.query(Regions).filter(Regions.courier_id == courier_id).all()]

        for order in delivery:
            intervals_delivery = sess.query(IntervalDelivery).filter(
                IntervalDelivery.order_id == order.order_id).all()
            intervals = sess.query(Interval).filter(Interval.courier_id == courier_id).all()

            suit_for_intervals = any([any(
                [interval_delivery.time_stop > interval.time_start and interval.time_stop > interval_delivery.time_start
                 for interval_delivery in intervals_delivery]) for interval in intervals])

            region = sess.query(OrderRegion).filter(OrderRegion.order_id == order.order_id).first().region
            suit_for_regions = region in courier_regions
            if not suit_for_intervals or not suit_for_regions:
                order.assign_time = None
                order.courier_id = None
                order.type_for_delivery = None
                sess.commit()

        delivery = list(filter(lambda x: x.courier_id is not None, delivery))
        sum_weight = sum([order.weight for order in delivery])
        i = 0
        while sum_weight > sess.query(CourierType).filter(CourierType.type == courier.courier_type).first().carrying:
            sum_weight -= delivery[i].weight
            delivery[i].assign_time = None
            delivery[i].courier_id = None
            delivery[i].type_for_delivery = None
            i += 1
            sess.commit()

        return make_response(jsonify({'courier_id': courier.courier_id, 'courier_type': courier.courier_type,
                                      'regions': [region.region for region in
                                                  sess.query(Regions).filter(Regions.courier_id == courier_id)],
                                      'working_hours': [f'{str(interval)}' for interval in
                                                        sess.query(Interval).filter(
                                                            Interval.courier_id == courier_id).all()]}), 200)

    def get(self, courier_id):
        try:
            courier_id = int(courier_id)
        except ValueError:
            abort(400)

        sess = create_session()
        courier = sess.query(Courier).filter(Courier.courier_id == courier_id).first()
        if not courier:
            abort(404)
        orders = sess.query(Order).filter(Order.courier_id == courier_id, Order.complete_time != None).all()
        regions = list(set([sess.query(OrderRegion).filter(OrderRegion.order_id == order.order_id).first().region
                            for order in orders]))
        av_time = {}
        rating = 0
        if orders:
            for region in regions:
                delivery = list(filter(lambda order: region in [reg.region for reg in
                                                                sess.query(OrderRegion).filter(
                                                                    OrderRegion.order_id == order.order_id).all()],
                                       orders))
                delivery = sorted(delivery, key=lambda order: order.complete_time)
                if delivery is None:
                    continue

                times = [(delivery[0].complete_time - delivery[0].assign_time).total_seconds()]
                for i in range(1, len(delivery)):
                    times.append((delivery[i].complete_time - delivery[i - 1].complete_time).total_seconds())
                av_time[region] = sum(times) / len(times)

            min_t = min(list(av_time.values()))
            rating = (3600 - min(min_t, 3600)) / 3600 * 5

        assign_times = [order.assign_time for order in
                        sess.query(Order.assign_time).filter(Order.courier_id == courier_id).distinct()]
        earnings = 0
        complete_delivery = 0
        for time in assign_times:
            delivery = sess.query(Order).filter(Order.assign_time == time).all()
            orders_complete = sess.query(Order).filter(Order.assign_time == time, Order.complete_time != None).all()
            if len(delivery) == len(orders_complete):
                complete_delivery += 1
                earnings += 500 * sess.query(CourierType).filter(
                    CourierType.type == delivery[0].type_for_delivery).first().coefficient

        if complete_delivery:
            return make_response(jsonify({'courier_id': courier_id,
                                          'courier_type': courier.courier_type,
                                          'regions': [reg.region for reg in sess.query(Regions).filter(
                                              Regions.courier_id == courier_id).all()],
                                          "working_hours": [str(hours) for hours in
                                                            sess.query(Interval).filter(
                                                                Interval.courier_id == courier_id).all()],
                                          "rating": rating,
                                          "earnings": earnings}), 200)

        return make_response(jsonify({'courier_id': courier_id,
                                      'courier_type': courier.courier_type,
                                      'regions': [reg.region for reg in
                                                  sess.query(Regions).filter(Regions.courier_id == courier_id).all()],
                                      "working_hours": [str(hours) for hours in
                                                        sess.query(Interval).filter(
                                                            Interval.courier_id == courier_id).all()],
                                      "earnings": earnings}), 200)
