from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.CustomerModel import Customer


class CustomerFactory(SQLAlchemyFactory[Customer]):
    __model__ = Customer
    __set_relationships__ = False

    status     = Use(lambda: True)

    created_at = Use(lambda: None)
    updated_at = Use(lambda: None)
