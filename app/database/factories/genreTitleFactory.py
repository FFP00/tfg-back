from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.GenreTitleModel import GenreTitle

fake = Faker(['es_ES'])

class GenreTitleFactory(SQLAlchemyFactory[GenreTitle]):
    __model__ = GenreTitle
    __set_relationships__ = False

    id          = Use(lambda: None)

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
