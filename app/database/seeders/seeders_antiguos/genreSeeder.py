import logging

from sqlmodel import Session

from app.database.factories.genreFactory import GenreFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_genres(session: Session, count: int):
    genres = []

    for _ in range(count):

        genre = GenreFactory.build()
        genres.append(genre)

    session.add_all(genres)
    logger.info(f"{count} generos preparados.")
