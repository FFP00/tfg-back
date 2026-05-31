from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pwdlib import PasswordHash

from app.database.models.CustomerModel import Customer

fake = Faker(['es_ES'])
password_hasher = PasswordHash.recommended()

class CustomerFactory(SQLAlchemyFactory[Customer]):
    __model__ = Customer
    __set_relationships__ = False

    id          = Use(lambda: None)
    status      = Use(lambda: True)

    name        = Use(fake.unique.user_name)
    email       = Use(fake.unique.email)
    password    = Use(lambda: password_hasher.hash("password123"))

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
