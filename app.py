from flask import Flask
from flask_restful import Api
from data import db_session
from os import mkdir
from waitress import serve
from os.path import exists
from data.couriers_type import CourierType
from resources.courier_resources import CouriersListResource, CouriersResource
from resources.order_resources import OrdersListResources, OrdersAssignResources, OrdersCompleteResources

app = Flask(__name__)
api = Api(app)


def add_courier_types():
    session = db_session.create_session()
    if sorted(type.type for type in session.query(CourierType).all()) != ['bike', 'car', 'foot']:
        session.query(CourierType).delete()
        session.commit()
        types = (('foot', 10, 2), ('bike', 15, 5), ('car', 50, 9))
        for title, carrying, coefficient in types:
            type = CourierType(type=title, carrying=carrying, coefficient=coefficient)
            session.add(type)
        session.commit()


api.add_resource(CouriersListResource, '/couriers')
api.add_resource(CouriersResource, '/couriers/<string:courier_id>')
api.add_resource(OrdersListResources, '/orders')
api.add_resource(OrdersAssignResources, '/orders/assign')
api.add_resource(OrdersCompleteResources, '/orders/complete')


def main():
    if not exists('./db'):
        mkdir('./db')
    db_session.global_init("db/base.db")
    add_courier_types()
    # app.run(debug=True, port=5000, host='127.0.0.1')
    serve(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
