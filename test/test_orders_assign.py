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


def test_succeed_assign_orders(client):
    sess = create_session()
    json = {
        'courier_id': 2
    }
    rv = client.post('/orders/assign', json=json)
    double_rv = client.post('/orders/assign', json=json)
    assert rv.status_code == 200
    assert double_rv.status_code == 200
    assert rv.data == double_rv.data
    data = loads(rv.data)
    assign_time = data['assign_time']
    ids = [dct['id'] for dct in data['orders']]
    t_ids = [1, 2]
    for id in ids:
        order = sess.query(Order).filter(Order.order_id == id).first()
        assert order.assign_time.isoformat() + 'Z' == assign_time
    assert t_ids == ids
    assert len(data['orders']) == 2


def test_wrong_courier_id(client):
    json = {
        'courier_id': 3
    }
    rv = client.post('/orders/assign', json=json)
    assert rv.status_code == 400
    assert loads(rv.data) == {}


def test_none_orders(client):
    json = {
        'courier_id': 1
    }
    rv = client.post('/orders/assign', json=json)
    assert rv.status_code == 200
    assert loads(rv.data) == {"orders": []}


def test_before_complete_order(client):
    sess = create_session()
    json_assign = {
        'courier_id': 2
    }
    client.post('/orders/assign', json=json_assign)
    json_complete = {
        'courier_id': 2,
        'order_id': 2,
        'complete_time': "2021-04-10T10:33:01.42Z"
    }
    client.post('/orders/complete', json=json_complete)
    rv_double_assign = client.post('/orders/assign', json=json_assign)
    assert rv_double_assign.status_code == 200
    data = loads(rv_double_assign.data)
    ids = [dct['id'] for dct in data['orders']]
    data = datetime.strptime(json_complete['complete_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
    assert ids == [1]
    assert sess.query(Order).filter(Order.order_id == 2).first().complete_time == data


def test_not_special_fields(client):
    sess = create_session()
    json = {
        'courier_id': 2,
        'afdfda': ''
    }
    rv = client.post('/orders/assign', json=json)
    assert rv.status_code == 400
    assert sess.query(Order).all() == sess.query(Order).filter(Order.assign_time == None).all()


def test_not_courier_id(client):
    sess = create_session()
    json = {}
    rv = client.post('/orders/assign', json=json)
    assert rv.status_code == 400
    assert sess.query(Order).all() == sess.query(Order).filter(Order.assign_time == None).all()
