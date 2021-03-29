from datetime import datetime
from json import loads
from os import mkdir
from os.path import exists
import pytest
from app import app
from data.couriers_type import CourierType
from data.db_session import create_session, SqlAlchemyBase
from data.db_session import global_init

if not exists('./db'):
    mkdir('./db')


def reset_db(engine):
    SqlAlchemyBase.metadata.drop_all(engine)
    SqlAlchemyBase.metadata.create_all(engine)


def add_order_success_get_courier_without_delivery():
    json_orders_12 = {"data": [
        {
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
        }
    ]}
    json_assign = {
        'courier_id': 1
    }
    client = app.test_client()
    client.post('/orders', json=json_orders_12)
    client.post('/orders/assign', json=json_assign)
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    json_complete_1 = {
        "courier_id": 1,
        "order_id": 1,
        "complete_time": now
    }
    client.post('/orders/complete', json=json_complete_1)


def add_delivery_success_get_courier():
    json_orders_12 = {"data": [
        {
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
        }
    ]}
    json_assign = {
        'courier_id': 1
    }
    json_orders_11 = {"data": [
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
        }]}
    client = app.test_client()
    client.post('/orders', json=json_orders_12)
    client.post('/orders/assign', json=json_assign)
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    json_complete_1 = {
        "courier_id": 1,
        "order_id": 1,
        "complete_time": now
    }
    json_complete_2 = {
        "courier_id": 1,
        "order_id": 2,
        "complete_time": now
    }
    client.post('/orders/complete', json=json_complete_1)
    client.post('/orders/complete', json=json_complete_2)
    client.post('/orders', json=json_orders_11)
    client.post('/orders/assign', json=json_assign)
    now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    json_complete_3 = {
        "courier_id": 1,
        "order_id": 3,
        "complete_time": now
    }
    json_complete_4 = {
        "courier_id": 1,
        "order_id": 4,
        "complete_time": now
    }
    client.post('/orders/complete', json=json_complete_3)
    client.post('/orders/complete', json=json_complete_4)


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
    engine = global_init('./db/test_base.db')
    add_types(create_session())
    add_courier()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

    reset_db(engine)


def test_success_get_courier(client):
    add_delivery_success_get_courier()
    rv = client.get('/couriers/1')
    data = loads(rv.data)
    assert rv.status_code == 200
    assert data['earnings'] == 9000
    assert round(data['rating']) == 5


def test_success_get_courier_without_delivery(client):
    add_order_success_get_courier_without_delivery()
    rv = client.get('/couriers/1')
    data = loads(rv.data)
    assert rv.status_code == 200
    assert data['earnings'] == 0
    assert 'rating' not in list(data.keys())


def test_wrong_courier_id(client):
    add_order_success_get_courier_without_delivery()
    rv = client.get('/couriers/1024')
    assert rv.status_code == 404
    rv = client.get('/couriers/adfadf32fd')
    assert rv.status_code == 400
