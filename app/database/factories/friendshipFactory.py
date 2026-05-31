from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.FriendshipModel import Friendship


class FriendshipFactory(SQLAlchemyFactory[Friendship]):
    __model__ = Friendship
    __set_relationships__ = False

    id         = Use(lambda: None)
    status     = Use(lambda: "pending")
    created_at = Use(lambda: None)
    updated_at = Use(lambda: None)
