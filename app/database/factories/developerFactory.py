from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pwdlib import PasswordHash

from app.database.models.DeveloperModel import Developer

fake = Faker(['es_ES'])
password_hasher = PasswordHash.recommended()

class DeveloperFactory(SQLAlchemyFactory[Developer]):
    __model__ = Developer
    __set_relationships__ = False

    id              = Use(lambda: None)
    status          = Use(lambda: True)

    name            = Use(fake.unique.company)
    email           = Use(fake.unique.email)
    support_email   = Use(fake.unique.email)
    password        = Use(lambda: password_hasher.hash("password123"))
    website_url     = Use(fake.url)

    created_at      = Use(lambda: None)
    updated_at      = Use(lambda: None)
