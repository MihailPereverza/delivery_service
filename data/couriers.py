from sqlalchemy import Column, String, Integer
from .db_session import SqlAlchemyBase, create_session
from sqlalchemy.orm import relation, validates
from .couriers_type import CourierType


class Courier(SqlAlchemyBase):
    __tablename__ = 'couriers'

    courier_id = Column(Integer, primary_key=True, autoincrement=True)
    courier_type = Column(String)
    # 1 - название класса, который ссылается сюда, 2 - название этого класса
    regions = relation('Regions', back_populates='courier')
    intervals = relation('Interval', back_populates='courier')
    orders = relation('Order', back_populates='courier')

    @validates('courier_id')
    def validate_courier_id(self, key, value):
        session = create_session()
        ids = [courier.courier_id for courier in session.query(Courier).all()]
        assert value not in ids and isinstance(value, int) and value > 0
        return value

    @validates('courier_type')
    def validate_courier_type(self, key, value):
        session = create_session()
        types = [courier_type.type for courier_type in session.query(CourierType).all()]
        assert value in types
        return value
