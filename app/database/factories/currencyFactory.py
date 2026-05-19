from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.CurrencyModel import Currency

fake = Faker(['es_ES'])

class CurrencyFactory(SQLAlchemyFactory[Currency]):
    __model__ = Currency

    id          = Use(lambda: None)
    name        = Use(fake.unique.currency_name)
    code        = Use(fake.unique.currency_code)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
