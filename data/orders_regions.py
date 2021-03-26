from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, validates, create_session
from .db_session import SqlAlchemyBase
from .orders import Order


class Order_region(SqlAlchemyBase):
    __tablename__ = 'orders_regions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(Integer, nullable=False)

    # здесь название таблицы на которую ссылаешься
    order_id = Column(Integer, ForeignKey('orders.order_id'))
    # здесь название класса, на который ссылаешься
    order = relation('Order')

    @validates('region')
    def validate_region(self, key, value):
        assert isinstance(value, int) and value > 0
        return value

    @validates('order_id')
    def validate_courier_id(self, key, value):
        session = create_session()
        return value

