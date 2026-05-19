from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.endpoint.models.MediaModel import Media

fake = Faker(['es_ES'])

class MediaFactory(SQLAlchemyFactory[Media]):
    __model__ = Media

    id              = Use(lambda: None)
    path_300x450    = Use(lambda: fake.image_url(width=300, height=450))
    path_600x900    = Use(lambda: fake.image_url(width=600, height=900))

    created_at      = Use(lambda: None)
    updated_at      = Use(lambda: None)
