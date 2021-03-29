from datetime import datetime
from json import loads
from os import mkdir
from os.path import exists
import pytest
from app import app
from data.couriers import Courier
from data.couriers_type import CourierType
from data.db_session import create_session, SqlAlchemyBase
from data.db_session import global_init
from data.intervals import Interval
from data.orders import Order
from data.regions import Regions


def reset_db(engine):
    SqlAlchemyBase.metadata.drop_all(engine)
    SqlAlchemyBase.metadata.create_all(engine)


def add_order():
    json = {"data": [{
        "order_id": 1,
        "weight": 3,
        "region": 12,
        "delivery_hours": ["09:00-10:00"]
    },
        {
            "order_id": 2,
            "weight": 4,
            "region": 12,
            "delivery_hours": ["11:00-12:00"]
        },
        {
            "order_id": 3,
            "weight": 5,
            "region": 11,
            "delivery_hours": ["13:00-14:00"]
        },
        {
            "order_id": 4,
            "weight": 6,
            "region": 11,
            "delivery_hours": ["15:00-16:00"]
        },
    ]}
    app.test_client().post('/orders', json=json)


def add_courier():
    json = {"data": [
        {
            "courier_id": 1,
            "courier_type": "car",
            "regions": [11, 12, 22],
            "working_hours": ["09:35-14:05", "14:30-17:00"]
        }
    ]}
    app.test_client().post('/couriers', json=json)


def add_types(session):
    types = (('foot', 10, 2), ('bike', 15, 5), ('car', 50, 9))
    for title, carrying, coefficient in types:
        typee = CourierType(type=title, carrying=carrying, coefficient=coefficient)
        session.add(typee)
    session.commit()


# функция которая будет выполняться перед началом тестов
@pytest.fixture(scope='function')
def client():
    if not exists('./db'):
        mkdir('./db')
    engine = global_init('./db/test_base.db')
    add_types(create_session())
    add_courier()
    add_order()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

    reset_db(engine)


def test_success_patch_courier(client):
    json = {
        "courier_type": "bike",
        "regions": [13],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    print(loads(rv.data))
    assert rv.data == b'{"courier_id":1,"courier_type":"bike","regions":[13],"working_hours":["05:00-06:00"]}\n'


def test_success_edit_courier_type_with_unassign_orders(client):
    sess = create_session()
    json_assign = {
        'courier_id': 1
    }
    rv_assign = client.post('/orders/assign', json=json_assign)
    print(rv_assign.data)
    json = {
        "courier_type": "foot"
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    rv_assign = client.post('/orders/assign', json=json_assign)
    data = loads(rv_assign.data)
    ids = list(sorted([dct['id'] for dct in data['orders']]))
    assert ids == [1, 2]
    assign_time = datetime.strptime(data['assign_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
    orders = sess.query(Order).filter(Order.assign_time == assign_time).all()
    assert len(orders) == 2
    ids = [order.order_id for order in orders]
    assert ids == [1, 2]


def test_success_edit_regions_with_unassign_orders(client):
    sess = create_session()
    json_assign = {
        'courier_id': 1
    }
    rv_assign = client.post('/orders/assign', json=json_assign)
    json = {
        "regions": [12, 22],
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    rv_assign = client.post('/orders/assign', json=json_assign)
    data = loads(rv_assign.data)
    ids = list(sorted([dct['id'] for dct in data['orders']]))
    assert ids == [1, 2]
    assign_time = datetime.strptime(data['assign_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
    orders = sess.query(Order).filter(Order.assign_time == assign_time).all()
    assert len(orders) == 2
    ids = [order.order_id for order in orders]
    assert ids == [1, 2]


def test_success_edit_working_hours_with_unassign_orders(client):
    sess = create_session()
    json_assign = {
        'courier_id': 1
    }
    client.post('/orders/assign', json=json_assign)
    json = {
        "working_hours": ["09:00-10:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    rv_assign = client.post('/orders/assign', json=json_assign)
    data = loads(rv_assign.data)
    ids = list(sorted([dct['id'] for dct in data['orders']]))
    assert ids == [1]
    assign_time = datetime.strptime(data['assign_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
    orders = sess.query(Order).filter(Order.assign_time == assign_time).all()
    assert len(orders) == 1
    ids = [order.order_id for order in orders]
    assert ids == [1]


def test_not_specified_fields(client):
    json_assign = {
        'courier_id': 1
    }
    client.post('/orders/assign', json=json_assign)
    json = {
        "working_hours": ["09:00-10:00"],
        'asfdfsdfdsfdfdfsdg': 3412545
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400


def test_not_fields(client):
    json_assign = {
        'courier_id': 1
    }
    client.post('/orders/assign', json=json_assign)
    json = {}
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400


def test_success_edit_courier_type(client):
    sess = create_session()
    json = {
        "courier_type": "bike"
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    print(loads(rv.data))
    assert loads(rv.data) == {"courier_id": 1,
                              "courier_type": "bike",
                              "regions": [11, 12, 22],
                              "working_hours": ["09:35-14:05", "14:30-17:00"]}
    courier = sess.query(Courier).first()
    assert courier.courier_type == 'bike'
    regions = [reg.region for reg in sess.query(Regions).filter(Regions.courier_id == 1).all()]
    regions = list(sorted(regions))
    assert regions == [11, 12, 22]
    working_hours = [str(interval) for interval in sess.query(Interval).filter(Interval.courier_id == 1).all()]
    print(working_hours)
    print(["9:35-14:05", "14:30-17:00"])
    print(set(working_hours) - set(["9:35-14:05", "14:30-17:00"]))
    assert set(working_hours) - set(["09:35-14:05", "14:30-17:00"]) == set()


def test_success_edit_regions(client):
    sess = create_session()
    json = {
        "regions": [2, 3, 4]

    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    print(loads(rv.data))
    assert loads(rv.data) == {"courier_id": 1,
                              "courier_type": "car",
                              "regions": [2, 3, 4],
                              "working_hours": ["09:35-14:05", "14:30-17:00"]}
    courier = sess.query(Courier).first()
    assert courier.courier_type == 'car'
    regions = [reg.region for reg in sess.query(Regions).filter(Regions.courier_id == 1).all()]
    regions = list(sorted(regions))
    assert regions == [2, 3, 4]
    working_hours = [str(interval) for interval in sess.query(Interval).filter(Interval.courier_id == 1).all()]
    assert set(working_hours) - set(["09:35-14:05", "14:30-17:00"]) == set()


def test_success_edit_working_hours(client):
    sess = create_session()
    json = {
        "working_hours": ["07:00-09:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 200
    print(loads(rv.data))
    assert rv.data == b'{"courier_id":1,"courier_type":"car","regions":[11,12,22],"working_hours":["07:00-09:00"]}\n'
    courier = sess.query(Courier).first()
    assert courier.courier_type == 'car'
    regions = [reg.region for reg in sess.query(Regions).filter(Regions.courier_id == 1).all()]
    regions = list(sorted(regions))
    assert regions == [11, 12, 22]
    working_hours = [str(interval) for interval in sess.query(Interval).filter(Interval.courier_id == 1).all()]
    assert set(working_hours) - set(["07:00-09:00"]) == set()


def check_stock_courier():
    sess = create_session()
    courier = sess.query(Courier).first()
    assert courier.courier_type == 'car'
    regions = [reg.region for reg in sess.query(Regions).filter(Regions.courier_id == 1).all()]
    regions = list(sorted(regions))
    assert regions == [11, 12, 22]
    working_hours = [str(interval) for interval in sess.query(Interval).filter(Interval.courier_id == 1).all()]
    assert set(working_hours) - set(["09:35-14:05", "14:30-17:00"]) == set()


def test_wrong_courier_working_hours(client):
    json = {
        "courier_type": "bike",
        "regions": [13],
        "working_hours": ["05fda:00-06:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    check_stock_courier()
    json = {
        "courier_type": "bike",
        "regions": [13],
        "working_hours": [""]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    check_stock_courier()
    json = {
        "courier_type": "bike",
        "regions": [13],
        "working_hours": "05:00-06:00"
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    check_stock_courier()
    json = {
        "courier_type": "bike",
        "regions": [13],
        "working_hours": ""
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    check_stock_courier()
    json = {
        "courier_type": "bike",
        "regions": [13],
        "working_hours": 13
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    check_stock_courier()


def test_wrong_courier_regions(client):
    json = {
        "courier_type": "bike",
        "regions": 13,
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1',
                      json=json)
    assert rv.status_code == 400
    json = {
        "courier_type": "bike",
        "regions": ["13", 12],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    json = {
        "courier_type": "bike",
        "regions": '',
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    json = {
        "courier_type": "bike",
        "regions": "fadsf",
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400
    json = {
        "courier_type": "bike",
        "regions": [],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1', json=json)
    assert rv.status_code == 400


def test_wrong_courier_type(client):
    json = {
        "courier_type": "moto",
        "regions": [13],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1',
                      json=json)
    assert rv.status_code == 400
    json = {
        "courier_type": "",
        "regions": [13],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1',
                      json=json)
    assert rv.status_code == 400

    json = {
        "courier_type": [],
        "regions": [13],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1',
                      json=json)
    assert rv.status_code == 400
    json = {
        "courier_type": ['car'],
        "regions": [13],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1',
                      json=json)
    assert rv.status_code == 400

    json = {
        "courier_type": 13,
        "regions": [13],
        "working_hours": ["05:00-06:00"]
    }
    rv = client.patch('/couriers/1',
                      json=json)
    assert rv.status_code == 400
