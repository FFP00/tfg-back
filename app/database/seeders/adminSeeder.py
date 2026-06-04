import logging

from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.database.models.CountryModel import Country
from app.database.models.UserModel import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hasher = PasswordHash.recommended()


def seed_admin(session: Session) -> None:
    if session.exec(select(User).where(User.email == "admin@burnt.com")).first():
        return

    spain = session.exec(select(Country).where(Country.code == "ES")).first()
    if not spain:
        spain = session.exec(select(Country)).first()
    if not spain:
        logger.error("No hay países disponibles para crear el admin")
        return

    session.add(
        User(
            name="admin",
            email="admin@burnt.com",
            password=hasher.hash("1234"),
            country_id=spain.id,
            type="ADM",
        )
    )
    logger.info("Admin preparado.")
