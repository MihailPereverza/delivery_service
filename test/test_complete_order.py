from datetime import datetime
from json import loads
import pytest
from app import app
from data.couriers_type import CourierType
from data.db_session import create_session, SqlAlchemyBase
from data.db_session import global_init
from data.orders import Order
from os import mkdir
from os.path import exists


def reset_db(engine):
    SqlAlchemyBase.metadata.drop_all(engine)
    SqlAlchemyBase.metadata.create_all(engine)


def add_order():
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 11,
        "delivery_hours": ["08:00-9:00"]
    },
        {
            "order_id": 2,
            "weight": 7,
            "region": 11,
            "delivery_hours": ["08:00-9:00"]
        },
        {
            "order_id": 3,
            "weight": 8,
            "region": 11,
            "delivery_hours": ["08:00-9:00"]
        }
    ]}

    app.test_client().post('/orders', json=json)


def add_courier():
    json = {"data": [
        {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [666],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        },
        {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": [11],
            "working_hours": ["11:35-14:05", "08:00-11:00"]
        },
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


def test_succeed_complete_order(client):
    sess = create_session()
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "courier_id": 2,
        "order_id": 2,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 200
    assert loads(rv.data)['order_id'] == 2
    date = datetime.strptime(json['complete_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
    assert sess.query(Order).filter(Order.order_id == 2).first().complete_time == date
    json_double = {
        "courier_id": 2,
        "order_id": 2,
        "complete_time": "2021-04-8T10:33:01.42Z"
    }
    rv_double = client.post('/orders/complete', json=json_double)
    assert rv.status_code == 200
    assert rv_double.status_code == 200
    assert loads(rv.data)['order_id'] == 2
    assert sess.query(Order).filter(Order.order_id == 2).first().complete_time == date


def test_complete_order_wrong_courier_id(client):
    sess = create_session()
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "courier_id": 666,
        "order_id": 2,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400
    order = sess.query(Order).filter(Order.order_id == 2).first()
    assert order.complete_time is None
    json = {
        "courier_id": 1,
        "order_id": 2,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400
    assert order.complete_time is None


def test_complete_order_not_assign_order(client):
    sess = create_session()
    json = {
        "courier_id": 2,
        "order_id": 2,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400
    order = sess.query(Order).filter(Order.order_id == 2).first()
    assert order.complete_time is None


def test_compelte_order_wrong_order_id(client):
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "courier_id": 2,
        "order_id": 6,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('orders/complete', json=json)
    assert rv.status_code == 400
    json = {
        "courier_id": 2,
        "order_id": 3,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400


def test_complete_order_wrong_complete_time(client):
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "courier_id": 2,
        "order_id": 3,
        "complete_time": "2021-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400


def test_absence_courier_id(client):
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "order_id": 2,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400


def test_absence_order_id(client):
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "courier_id": 2,
        "complete_time": "2021-04-10T10:33:01.42Z"
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400


def test_absence_complete_time(client):
    json = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json)
    json = {
        "courier_id": 2,
        "order_id": 2
    }
    rv = client.post('/orders/complete', json=json)
    assert rv.status_code == 400
