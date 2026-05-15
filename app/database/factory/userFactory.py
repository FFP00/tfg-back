from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pwdlib import PasswordHash

from app.database.model.User import User

fake = Faker(['es_ES'])
password_hasher = PasswordHash.recommended()

class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __set_relationships__ = False

    id          = Use(lambda: None)
    status      = Use(lambda: True)


    name      = Use(fake.first_name)
    lastname  = Use(fake.last_name)
    dni       = Use(lambda: fake.unique.bothify("########?").upper())
    email  = Use(fake.unique.email)
    password  = Use(lambda: password_hasher.hash("password123"))

    updated_at  = Use(lambda: None)
    created_at  = Use(lambda: None)
