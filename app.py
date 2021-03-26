from flask import Flask
from flask_restful import Api
import os

from data import db_session
from resources.courier_resources import CouriersListResource, CouriersResource
from resources.order_resources import OrdersListResources, OrdersAssignResources, OrdersCompleteResources

app = Flask(__name__)


def main():
    db_session.global_init("db/base.db")

    api = Api(app)
    api.add_resource(CouriersListResource, '/couriers')
    api.add_resource(CouriersResource, '/couriers/<string:courier_id>')
    api.add_resource(OrdersListResources, '/orders')
    api.add_resource(OrdersAssignResources, '/orders/assign')
    api.add_resource(OrdersCompleteResources, '/orders/complete')
    app.run(debug=True, port=5000, host='127.0.0.1')


if __name__ == '__main__':
    main()
