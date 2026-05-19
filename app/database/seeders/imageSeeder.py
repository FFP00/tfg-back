import logging

from sqlmodel import Session

from app.database.factories.imageFactory import ImageFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_images(session: Session, count: int):
    images = []

    for _ in range(count):

        image = ImageFactory.build()
        images.append(image)

    session.add_all(images)
    logger.info(f"{count} imagenes preparados.")
