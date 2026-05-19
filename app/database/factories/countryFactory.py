from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.CountryModel import Country

fake = Faker(['es_ES'])

class CountryFactory(SQLAlchemyFactory[Country]):
    __model__ = Country
    __set_relationships__ = False

    id          = Use(lambda: None)
    name        = Use(fake.unique.country)
    code        = Use(fake.unique.country_code)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
