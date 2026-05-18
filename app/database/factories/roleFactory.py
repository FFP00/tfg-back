from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.RoleModel import Role

fake = Faker(['es_ES'])

class RoleFactory(SQLAlchemyFactory[Role]):
    __model__ = Role
    id = Use(lambda: None)

    name      = Use(fake.unique.job)
    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
