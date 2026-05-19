import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.developerFactory import DeveloperFactory
from app.endpoint.models.ImageModel import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_developers(session: Session, count: int):
    developers = []
    images = session.exec(select(Image.id)).all()

    if not images:
        logger.info("No encontramos imagenes")
        return

    for _ in range(count):
        image = secrets.choice(images)

        developer = DeveloperFactory.build()
        developer.image_id=image
        developers.append(developer)

    session.add_all(developers)
    logger.info(f"{count} desarrolladores preparados.")
