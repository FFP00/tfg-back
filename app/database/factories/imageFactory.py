from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.ImageModel import Image


class ImageFactory(SQLAlchemyFactory[Image]):
    __model__ = Image

    id         = Use(lambda: None)
    profile    = Use(lambda: None)
    banner     = Use(lambda: None)

    created_at = Use(lambda: None)
    updated_at = Use(lambda: None)
