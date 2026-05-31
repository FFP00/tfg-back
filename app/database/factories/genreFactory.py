from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.database.models.GenreModel import Genre

fake = Faker(['es_ES'])

GENRES = [
    "Acción", "Aventura", "RPG", "Estrategia", "Deportes",
    "Carreras", "Simulación", "Terror", "Puzzle", "Plataformas",
    "Lucha", "Shooter", "Música", "Casual", "Indie",
]

_genre_iter = iter(GENRES)

class GenreFactory(SQLAlchemyFactory[Genre]):
    __model__ = Genre

    id          = Use(lambda: None)
    name        = Use(lambda: next(_genre_iter))

    created_at  = Use(lambda: None)
    updated_at  = Use(lambda: None)
