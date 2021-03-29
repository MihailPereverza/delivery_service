from datetime import datetime
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


class OrdersListResources(Resource):
    def post(self):
        sess = create_session()
        keys = ['order_id', 'weight', 'region', 'delivery_hours']
        not_validate_orders = []
        validate_object = []

        for order_data in request.get_json()['data']:
            if not all(key in keys for key in order_data) or len(keys) != len(order_data):
                not_validate_orders.append(order_data['order_id'])
                continue
            if not isinstance(order_data['delivery_hours'], list):
                not_validate_orders.append(order_data['order_id'])
                continue

            try:
                order = Order(order_id=order_data['order_id'], weight=order_data['weight'])
                region = OrderRegion(order_id=order_data['order_id'], region=order_data['region'])
                intervals = [IntervalDelivery(order_id=order_data['order_id'],
                                              time_start=time, time_stop=time)
                             for time in order_data['delivery_hours']]

                validate_object.extend([order] + [region] + intervals)
            except (AssertionError, ValueError, IndexError, TypeError):
                not_validate_orders.append(order_data['order_id'])

        if not_validate_orders:
            return make_response(
                jsonify({'validation_error': {'orders': [{'id': courier_id} for courier_id in not_validate_orders]}}),
                400)

        for new_object in validate_object:
            sess.add(new_object)
        sess.commit()
        return make_response(jsonify(
            {'orders': [{'id': order.order_id}
                        for order in filter(lambda x: isinstance(x, Order), validate_object)]}), 201)


class OrdersAssignResources(Resource):
    def post(self):
        sess = create_session()
        keys = ['courier_id']
        data = request.get_json()
        orders_for_courier = []

        if not all(key in keys for key in data) or len(keys) != len(data) or not isinstance(data['courier_id'], int):
            return make_response(jsonify(), 400)

        courier_id = data['courier_id']
        courier = sess.query(Courier).filter(Courier.courier_id == courier_id).first()
        if courier is None:
            return make_response(jsonify(), 400)

        intervals = sess.query(Interval).filter(Interval.courier_id == courier_id).all()
        regions_courier = [region.region
                           for region in sess.query(Regions).filter(Regions.courier_id == courier_id).all()]
        orders = sess.query(Order).filter(Order.courier_id == None).all()
        now = datetime.now()
        delivery = sess.query(Order).filter(Order.courier_id == courier_id, Order.complete_time == None).all()
        orders = sorted(orders, key=lambda order: order.weight)

        if delivery:
            now = delivery[0].assign_time
            orders_for_courier = [order.order_id for order in delivery]

        else:
            orders = sorted(orders, key=lambda order: order.weight)
            sum_weight = 0
            for order in orders:
                order_regions = [order_region.region for order_region
                                 in sess.query(OrderRegion).filter(OrderRegion.order_id == order.order_id).all()]

                intervals_delivery = sess.query(IntervalDelivery).filter(IntervalDelivery.order_id == order.order_id)
                suit_for_intervals = any([any(
                    [interval_delivery.time_stop > interval.time_start and
                     interval.time_stop > interval_delivery.time_start
                     for interval_delivery in intervals_delivery]) for interval in intervals])
                courier_carrying = sess.query(CourierType).filter(CourierType.type ==
                                                                  courier.courier_type).first().carrying
                suit_for_weight = (sum_weight + order.weight) <= courier_carrying
                suit_for_region = set([]) != (set(order_regions) & set(regions_courier))
                if suit_for_region and suit_for_weight and suit_for_intervals:
                    order = sess.query(Order).filter(Order.order_id == order.order_id).first()
                    order.courier_id = courier_id
                    order.assign_time = now
                    order.type_for_delivery = courier.courier_type
                    sum_weight += order.weight
                    # sess.add(order)
                    orders_for_courier.append(order.order_id)
                    sess.commit()

        if not orders_for_courier:
            return make_response(jsonify({'orders': []}), 200)
        return make_response(jsonify(
            dict(orders=[{'id': order_id} for order_id in orders_for_courier], assign_time=now.isoformat() + 'Z')), 200)


class OrdersCompleteResources(Resource):
    def post(self):
        sess = create_session()
        keys = ['courier_id', 'order_id', 'complete_time']
        data = request.get_json()
        try:
            if not all(key in keys for key in data) or len(keys) != len(data):
                return abort(400)
            if not isinstance(data['courier_id'], int) and not isinstance(data['order_id'], int):
                abort(400)
            order = sess.query(Order).filter(Order.order_id == data['order_id']).first()
            if order is None or order.courier_id != data['courier_id']:
                abort(400)

            data['complete_time'] = datetime.strptime(data['complete_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if order.assign_time > data['complete_time'] and order.complete_time is None:
                print('zdes')
                abort(400)
            if order.complete_time is None:
                order.complete_time = data['complete_time']
            sess.commit()
        except Exception:
            abort(400)

        return make_response(jsonify({'order_id': order.order_id}))
