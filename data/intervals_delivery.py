from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Time
from sqlalchemy.orm import relation, validates

from .db_session import SqlAlchemyBase


class IntervalDelivery(SqlAlchemyBase):
    __tablename__ = 'Intervals_delivery'

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_start = Column(Time, nullable=False)
    time_stop = Column(Time, nullable=False)
    order_id = Column(Integer, ForeignKey('orders.order_id'))

    # здесь название класса, на который ссылаешься
    order = relation('Order')

    @validates('time_start')
    def validate_time_start(self, key, value: str):
        assert isinstance(value, str)
        value = value.split('-')
        time_stop = datetime.strptime(value[1], '%H:%M')
        time_start = datetime.strptime(value[0], '%H:%M')
        assert time_stop > time_start
        value = datetime.strptime(value[0], '%H:%M').time()
        return value

    @validates('time_stop')
    def validate_time_stop(self, key, value: str):
        assert isinstance(value, str)
        value = value.split('-')
        time_stop = datetime.strptime(value[1], '%H:%M')
        time_start = datetime.strptime(value[0], '%H:%M')
        assert time_stop > time_start
        value = datetime.strptime(value[1], '%H:%M').time()
        return value

    @validates('order_id')
    def validate_order_id(self, key, value):
        assert isinstance(value, int)
        return value

    def __str__(self):
        return f'{self.time_start.strftime("%H:%M")}-{self.time_stop.strftime("%H:%M")}'
