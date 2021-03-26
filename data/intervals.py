from sqlalchemy import Column, Integer, ForeignKey, Time
from sqlalchemy.orm import relation, validates
from .db_session import SqlAlchemyBase
from datetime import datetime


class Interval(SqlAlchemyBase):
    __tablename__ = 'Intervals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_start = Column(Time, nullable=False)
    time_stop = Column(Time, nullable=False)
    courier_id = Column(Integer, ForeignKey('couriers.courier_id'))

    # здесь название класса, на который ссылаешься
    courier = relation('Courier')

    @validates('time_start')
    def validate_time_start(self, key, value: str):
        assert isinstance(value, str)
        value = value.split('-')
        value = datetime.strptime(value[0], '%H:%M').time()
        return value

    @validates('time_stop')
    def validate_time_stop(self, key, value: str):
        assert isinstance(value, str)
        value = value.split('-')
        value = datetime.strptime(value[1], '%H:%M').time()
        return value
