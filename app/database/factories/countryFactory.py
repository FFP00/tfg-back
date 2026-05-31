from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.CountryModel import Country

fake = Faker(['es_ES'])

class CountryFactory(SQLAlchemyFactory[Country]):
    __model__ = Country
    __set_relationships__ = False

    id          = Use(lambda: None)
    name        = Use(lambda: None)
    en_name     = Use(lambda: None)
    code        = Use(lambda: None)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
