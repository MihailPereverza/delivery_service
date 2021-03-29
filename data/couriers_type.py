from sqlalchemy import Column, String, Integer
from .db_session import SqlAlchemyBase


class CourierType(SqlAlchemyBase):
    __tablename__ = 'couriers_type'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    type = Column(String, nullable=False)
    carrying = Column(Integer, nullable=False)
    coefficient = Column(Integer, nullable=False)
