from datetime import datetime

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.model.Role import Role

fake = Faker(['es_ES'])

class RoleFactory(SQLAlchemyFactory[Role]):
    __model__ = Role
    id          = None
    updated_at  = Use(datetime.now)

    name      = Use(fake.job)
    created_at  = Use(datetime.now)
