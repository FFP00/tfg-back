import logging

from sqlmodel import Session

from app.database.factories.mediaFactory import MediaFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_medias(session: Session, count: int):
    medias = []

    for _ in range(count):

        media = MediaFactory.build()
        medias.append(media)

    session.add_all(medias)
    logger.info(f"{count} media preparados.")
