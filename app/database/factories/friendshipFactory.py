from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.FriendshipModel import Friendship

fake = Faker(['es_ES'])

class FriendshipFactory(SQLAlchemyFactory[Friendship]):
    __model__ = Friendship
    __set_relationships__ = False

    id          = Use(lambda: None)
    status      = Use(lambda: False)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
