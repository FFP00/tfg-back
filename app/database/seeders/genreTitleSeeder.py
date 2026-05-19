import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.genreTitleFactory import GenreTitleFactory
from app.endpoint.models.GenreModel import Genre
from app.endpoint.models.TitleModel import Title

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_genres_titles(session: Session, count: int):
    genres_titles = []
    genres = session.exec(select(Genre.id)).all()
    titles = session.exec(select(Title.id)).all()

    if not genres:
        logger.info("No encontramos generos")
        return

    if not titles:
        logger.info("No encontramos juegos")
        return

    for _ in range(count):
        genre = secrets.choice(genres)
        title = secrets.choice(titles)

        genre_title = GenreTitleFactory.build()
        genre_title.title_id=title
        genre_title.genre_id = genre
        genres_titles.append(genre_title)

    session.add_all(genres_titles)
    logger.info(f"{count} genre_title preparados.")
