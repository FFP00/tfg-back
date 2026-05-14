from datetime import datetime

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pwdlib import PasswordHash

from app.database.model.User import User

fake = Faker(['es_ES'])
password_hasher = PasswordHash.recommended()

class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    id          = None
    status      = True
    role_id     = None
    updated_at  = Use(datetime.now)
    created_at  = Use(datetime.now)

    name      = Use(fake.first_name)
    lastname  = Use(fake.last_name)
    dni       = Use(lambda: fake.unique.bothify("########?").upper())
    email  = Use(fake.unique.email)
    password  = Use(lambda: password_hasher.hash("password123"))
