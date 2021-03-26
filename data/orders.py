from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relation, validates
from .couriers import Courier
from .couriers_type import Courier_type
from .db_session import SqlAlchemyBase, create_session


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    weight = Column(Float)
    assign_time = Column(DateTime)
    complete_time = Column(DateTime)
    courier_id = Column(Integer, ForeignKey('couriers.courier_id'))
    type_for_delivery = Column(String)

    # 1 - название класса, который ссылается сюда, 2 - название этого класса
    regions = relation('Order_region', back_populates='order')
    intervals = relation('Interval_delivery', back_populates='order')
    courier = relation('Courier')

    @validates('order_id')
    def validate_order_id(self, key, value):
        session = create_session()
        ids = [order.order_id for order in session.query(Order).all()]
        assert value not in ids and isinstance(value, int) and value > 0
        return value

    @validates('weight')
    def validate_weight(self, key, value):
        assert isinstance(value, (float, int)) and 50 >= value >= 0.01
        return value

    @validates('courier_id')
    def validate_courier_id(self, key, value):
        session = create_session()
        ids = [courier.courier_id for courier in session.query(Courier).all()]
        assert (value in ids and isinstance(value, int)) or value is None
        return value

    @validates('type_for_delivery')
    def validate_courier_type(self, key, value):
        session = create_session()
        types = [courier_type.type for courier_type in session.query(Courier_type).all()]
        assert value in types or value is None
        return value
