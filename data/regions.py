from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, validates, create_session
from .db_session import SqlAlchemyBase
from .couriers import Courier


class Regions(SqlAlchemyBase):
    __tablename__ = 'regions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(Integer, nullable=False)
    # здесь название таблицы на которую ссылаешься
    courier_id = Column(Integer, ForeignKey('couriers.courier_id'))

    # здесь название класса, на который ссылаешься
    courier = relation('Courier')

    @validates('region')
    def validate_region(self, key, value):
        assert isinstance(value, int) and value > 0
        return value

    @validates('courier_id')
    def validate_courier_id(self, key, value):
        assert isinstance(value, int) and value > 0
        return value

