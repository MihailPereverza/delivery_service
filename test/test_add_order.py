import pytest
from app import app
from data.couriers_type import CourierType
from data.db_session import create_session, SqlAlchemyBase
from data.db_session import global_init
from data.intervals_delivery import IntervalDelivery
from data.orders import Order
from data.orders_regions import OrderRegion
from os import mkdir
from os.path import exists


def reset_db(engine):
    SqlAlchemyBase.metadata.drop_all(engine)
    SqlAlchemyBase.metadata.create_all(engine)


def add_courier():
    json = {"data": [
        {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        }
    ]}

    app.test_client().post('/couriers', json=json)


def add_types(session):
    types = (('foot', 10, 2), ('bike', 15, 5), ('car', 50, 9))
    for title, carrying, coefficient in types:
        type = CourierType(type=title, carrying=carrying, coefficient=coefficient)
        session.add(type)
    session.commit()


# функция которая будет выполняться перед началом тестов
@pytest.fixture(scope='function')
def client():
    if not exists('./db'):
        mkdir('./db')
    engine = global_init('./db/test_base.db')
    add_types(create_session())
    add_courier()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

    reset_db(engine)


def test_succeed_add_order(client):
    sess = create_session()
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 12,
        "delivery_hours": ["09:00-18:00"]
    }]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 201
    assert rv.data == b'{"orders":[{"id":1}]}\n'
    for order_data in json['data']:
        order = sess.query(Order).filter(Order.order_id == order_data['order_id']).first()
        o_regions = [reg.region for reg in
                     sess.query(OrderRegion).filter(OrderRegion.order_id == order.order_id).all()]
        o_hours = [str(i) for i in
                   sess.query(IntervalDelivery).filter(IntervalDelivery.order_id == order.order_id).all()]
        assert order is not None
        assert order.weight == order_data['weight']
        assert sorted(o_regions) == [order_data['region']]
        assert sorted(o_hours) == sorted(order_data['delivery_hours'])
        assert order.courier_id is None
        assert order.complete_time is None
        assert order.assign_time is None
        assert order.type_for_delivery is None


def test_wrong_order_id(client):
    sess = create_session()
    json_good = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 12,
        "delivery_hours": ["09:00-18:00"]
    }]}
    json_wrong = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 12,
        "delivery_hours": ["09:00-18:00"]
    },
        {
            "order_id": "2",
            "weight": 0.23,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        }
    ]}
    client.post('/orders', json=json_good)
    rv = client.post('/orders', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1},{"id":"2"}]}}\n'
    assert sess.query(Order).all()[0].order_id == 1
    assert len(sess.query(Order).all()) == 1
    assert len(create_session().query(OrderRegion).all()) == 1
    assert len(create_session().query(IntervalDelivery).all()) == 1
    order_data = json_good['data'][0]
    order = sess.query(Order).filter(Order.order_id == order_data['order_id']).first()
    o_regions = [reg.region for reg in
                 sess.query(OrderRegion).filter(OrderRegion.order_id == order.order_id).all()]
    o_hours = [str(i) for i in sess.query(IntervalDelivery).filter(IntervalDelivery.order_id == order.order_id).all()]
    assert sorted(o_regions) == [order_data['region']]
    assert sorted(o_hours) == sorted(order_data['delivery_hours'])


def test_wrong_weight(client):
    json = {"data": [{
        "order_id": 1,
        "weight": 'dfaf',
        "region": 12,
        "delivery_hours": ["09:00-18:00"]
    },
        {
            "order_id": 2,
            "weight": 0.235,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 3,
            "weight": 0,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 4,
            "weight": 50.01,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 5,
            "weight": 50.0000,
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 6,
            "weight": '15',
            "region": 12,
            "delivery_hours": ["09:00-18:00"]
        }, ]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1},{"id":2},{"id":3},{"id":4},{"id":6}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0


def test_wrong_region(client):
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 'dfa',
        "delivery_hours": ["09:00-18:00"]
    },
        {
            "order_id": 2,
            "weight": 0.23,
            "region": '1',
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 3,
            "weight": 0.23,
            "region": [1],
            "delivery_hours": ["09:00-18:00"]
        },
        {
            "order_id": 4,
            "weight": 0.23,
            "region": [1, 2],
            "delivery_hours": ["09:00-18:00"]
        },
    ]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1},{"id":2},{"id":3},{"id":4}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0


def test_wrong_delivery_hours(client):
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 13,
        "delivery_hours": ["09afdfd:00-18:00"]
    },
        {
            "order_id": 2,
            "weight": 0.23,
            "region": 13,
            "delivery_hours": "09:00-18:00"
        },
        {
            "order_id": 3,
            "weight": 0.23,
            "region": 13,
            "delivery_hours": ["09:00"]
        },
        {
            "order_id": 4,
            "weight": 0.23,
            "region": 13,
            "delivery_hours": ["09:00-18:00", "fegfsdgfd"]
        },
        {
            "order_id": 5,
            "weight": 0.23,
            "region": 13,
            "delivery_hours": 13
        },
        {
            "order_id": 6,
            "weight": 0.23,
            "region": 13,
            "delivery_hours": 'fadsf'
        },
        {
            "order_id": 7,
            "weight": 0.23,
            "region": 13,
            "delivery_hours": ''
        }]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == \
           b'{"validation_error":{"orders":[{"id":1},{"id":2},{"id":3},{"id":4},{"id":5},{"id":6},{"id":7}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0


def test_not_specified_fields(client):
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 13,
        "delivery_hours": ["09:00-18:00"],
        "dafdasf": 234
    },
    ]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0


def test_absence_order_weight(client):
    json = {"data": [{
        "order_id": 1,
        "region": 13,
        "delivery_hours": ["09:00-18:00"]
    },
    ]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0


def test_absence_order_region(client):
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "delivery_hours": ["09:00-18:00"],
    },
    ]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0


def test_absence_order_delivery_hours(client):
    json = {"data": [{
        "order_id": 1,
        "weight": 0.23,
        "region": 13,
    },
    ]}
    rv = client.post('/orders', json=json)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"orders":[{"id":1}]}}\n'
    assert len(create_session().query(Order).all()) == 0
    assert len(create_session().query(OrderRegion).all()) == 0
    assert len(create_session().query(IntervalDelivery).all()) == 0
