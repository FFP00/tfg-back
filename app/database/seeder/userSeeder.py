import logging
import secrets

from sqlmodel import Session, select

from app.database.factory.userFactory import UserFactory
from app.database.model.Role import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_users(session: Session, count: int):
    users = []
    roles = session.exec(select(Role.id)).all()

    for _ in range(count):
        role = secrets.choice(roles)

        if not roles:
            logger.info("Saltando usuarios")
            return

        user = UserFactory.build(role_id=role)
        users.append(user)

    session.add_all(users)
    logger.info(f"   -> {count} usuarios preparados.")
