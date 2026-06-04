from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.DeveloperModel import Developer

fake = Faker(["es_ES"])


class DeveloperFactory(SQLAlchemyFactory[Developer]):
    __model__ = Developer
    __set_relationships__ = False

    status          = Use(lambda: True)
    support_email   = Use(fake.unique.email)
    website_url     = Use(lambda: f"https://{fake.unique.domain_name()}")

    created_at      = Use(lambda: None)
    updated_at      = Use(lambda: None)
