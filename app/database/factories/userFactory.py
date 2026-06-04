from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from pwdlib import PasswordHash

from app.database.models.UserModel import User

fake = Faker(["es_ES"])
password_hasher = PasswordHash.recommended()


class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __set_relationships__ = False

    id          = Use(lambda: None)
    name        = Use(fake.unique.user_name)
    email       = Use(fake.unique.email)
    password    = Use(lambda: password_hasher.hash("password123"))
    type        = Use(lambda: "CUS")
    country_id  = Use(lambda: None)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
