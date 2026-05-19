from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.ImageModel import Image

fake = Faker(['es_ES'])

class ImageFactory(SQLAlchemyFactory[Image]):
    __model__ = Image

    id              = Use(lambda: None)
    path_256x256    = Use(lambda: fake.image_url(width=256, height=256))
    path_512x512    = Use(lambda: fake.image_url(width=512, height=512))

    created_at      = Use(lambda: None)
    updated_at      = Use(lambda: None)
