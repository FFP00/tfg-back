from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.CustomerTitleModel import CustomerTitle

fake = Faker(['es_ES'])

class CustomerTitleFactory(SQLAlchemyFactory[CustomerTitle]):
    __model__ = CustomerTitle
    __set_relationships__ = False

    id          = Use(lambda: None)
    playtime    = Use(lambda: fake.random_int(min=0, max=10000))

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
