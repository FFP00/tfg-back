from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.MediaModel import Media

fake = Faker(["es_ES"])

_PLACEHOLDER = b"\xff\xd8\xff\xe0" + b"\x00" * 16  # minimal JPEG-like placeholder


class MediaFactory(SQLAlchemyFactory[Media]):
    __model__ = Media
    __set_relationships__ = False

    id       = Use(lambda: None)
    capsule  = Use(lambda: _PLACEHOLDER)
    header   = Use(lambda: _PLACEHOLDER)
    store_1  = Use(lambda: _PLACEHOLDER)
    store_2  = Use(lambda: None)
    store_3  = Use(lambda: None)
    store_4  = Use(lambda: None)
    store_5  = Use(lambda: None)
    store_6  = Use(lambda: None)
    trailer  = Use(lambda: None)

    created_at = Use(lambda: None)
    updated_at = Use(lambda: None)
