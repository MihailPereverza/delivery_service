from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import validates
from .db_session import SqlAlchemyBase


class CourierType(SqlAlchemyBase):
    __tablename__ = 'couriers_type'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    type = Column(String, nullable=False)
    carrying = Column(Integer, nullable=False)
    coefficient = Column(Integer, nullable=False)

    @validates('type')
    def validate_courier_id(self, key, value):
        assert isinstance(value, str)
        return value

    @validates('carrying')
    def validate_carrying(self, key, value):
        assert isinstance(value, int)
        return value

    @validates('coefficient')
    def validate_coefficient(self, key, value):
        assert isinstance(value, int)
        return value
