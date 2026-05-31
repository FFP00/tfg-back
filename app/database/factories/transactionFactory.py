from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.TransactionModel import Transaction

fake = Faker(['es_ES'])

class TransactionFactory(SQLAlchemyFactory[Transaction]):
    __model__ = Transaction
    __set_relationships__ = False

    id          = Use(lambda: None)
    customer_id = Use(lambda: None)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
