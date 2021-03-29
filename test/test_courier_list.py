import pytest
from os import mkdir
from os.path import exists
from app import app
from data.couriers import Courier
from data.couriers_type import CourierType
from data.db_session import create_session, SqlAlchemyBase
from data.db_session import global_init
from data.intervals import Interval
from data.regions import Regions


def reset_db(engine):
    SqlAlchemyBase.metadata.drop_all(engine)
    SqlAlchemyBase.metadata.create_all(engine)


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
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    reset_db(engine)


def test_success_add_couriers(client):
    # create_engine()
    sess = create_session()
    json = {"data": [
        {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 12, 22],
            "working_hours": ["11:35-14:05", "09:00-11:00"]
        },
        {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": [22],
            "working_hours": ["09:00-18:00"]
        },
        {
            "courier_id": 3,
            "courier_type": "car",
            "regions": [12, 22, 23, 33],
            "working_hours": ["09:00-18:00"]
        }
    ]}
    rv = client.post('/couriers', json=json)
    assert rv.status_code == 201
    assert rv.data == b'{"couriers":[{"id":1},{"id":2},{"id":3}]}\n'
    for courier_data in json['data']:
        courier = sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first()
        c_regions = [reg.region for reg in sess.query(Regions).filter(Regions.courier_id == courier.courier_id).all()]
        c_hours = [str(i) for i in sess.query(Interval).filter(Interval.courier_id == courier.courier_id).all()]
        assert courier is not None
        assert courier.courier_type == courier_data['courier_type']
        assert sorted(c_regions) == sorted(courier_data['regions'])
        assert sorted(c_hours) == sorted(courier_data['working_hours'])


def test_wrong_courier_id(client):
    json_good = {'data': [{
        "courier_id": 1,
        "courier_type": "foot",
        "regions": [1, 12, 22],
        "working_hours": ["11:35-14:05", "09:00-11:00"]
    }]}
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "bike",
        "regions": [3],
        "working_hours": ["07:00-08:00"]
    },
        {
            "courier_id": "2",
            "courier_type": "bike",
            "regions": [3],
            "working_hours": ["07:00-08:00"]
        }]}
    client.post('/couriers', json=json_good)
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1},{"id":"2"}]}}\n'


def test_wrong_courier_type(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "sdffa",
        "regions": [3],
        "working_hours": ["07:00-08:00"]
    },
        {
            "courier_id": 2,
            "courier_type": 3,
            "regions": [3],
            "working_hours": ["07:00-08:00"]
        }]}
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1},{"id":2}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None


def test_wrong_regions(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "bike",
        "regions": ["3"],
        "working_hours": ["07:00-08:00"]
    },
        {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": 3,
            "working_hours": ["07:00-08:00"]
        },
        {
            "courier_id": 3,
            "courier_type": "bike",
            "regions": '',
            "working_hours": ["07:00-08:00"]
        },
    ]}
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1},{"id":2},{"id":3}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None


def test_wrong_working_hours(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "bike",
        "regions": [3],
        "working_hours": ["07fasdffdasfds:00-08:00"]
    },
        {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": [3],
            "working_hours": [5342543]
        },
        {
            "courier_id": 3,
            "courier_type": "bike",
            "regions": [3],
            "working_hours": "07:00-08:00"
        }, {
            "courier_id": 4,
            "courier_type": "bike",
            "regions": [3],
            "working_hours": "7"
        },
        {
            "courier_id": 5,
            "courier_type": "bike",
            "regions": [3],
            "working_hours": ""
        }]}
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1},{"id":2},{"id":3},{"id":4},{"id":5}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None


def test_not_specified_fields(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "foot",
        "regions": [1, 12, 22],
        "working_hours": ["11:35-14:05", "09:00-11:00"],
        "dsfaaffadsf": 452454
    }]}
    # client.post('/couriers', json=json_good)
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None


def test_absence_courier_courier_type(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "regions": [1, 12, 22],
        "working_hours": ["11:35-14:05", "09:00-11:00"]
    }]}
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None


def test_absence_courier_regions(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "foot",
        "working_hours": ["11:35-14:05", "09:00-11:00"]
    }]}
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None


def test_absence_courier_working_hours(client):
    sess = create_session()
    json_wrong = {'data': [{
        "courier_id": 1,
        "courier_type": "bike",
        "regions": [3]
    },
        {
            "courier_id": 2,
            "courier_type": "bike",
            "regions": [3]
    }]}
    rv = client.post('/couriers', json=json_wrong)
    assert rv.status_code == 400
    assert rv.data == b'{"validation_error":{"couriers":[{"id":1},{"id":2}]}}\n'
    for courier_data in json_wrong['data']:
        assert sess.query(Courier).filter(Courier.courier_id == courier_data['courier_id']).first() is None
