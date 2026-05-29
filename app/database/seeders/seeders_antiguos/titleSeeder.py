import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.titleFactory import TitleFactory
from app.endpoint.models.DeveloperModel import Developer
from app.endpoint.models.MediaModel import Media

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_titles(session: Session, count: int):
    titles = []
    developers = session.exec(select(Developer.id)).all()
    medias = session.exec(select(Media.id)).all()

    if not developers:
        logger.info("No encontramos desarrolladores")
        return

    if not medias:
        logger.info("No encontramos media's")
        return

    for _ in range(count):
        developer = secrets.choice(developers)
        media = secrets.choice(medias)

        title = TitleFactory.build()
        title.developer_id= developer
        title.media_id= media
        titles.append(title)

    session.add_all(titles)
    logger.info(f"{count} titulos preparados.")
