import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.userFactory import UserFactory
from app.endpoint.models.RoleModel import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_users(session: Session, count: int):
    users = []
    roles = session.exec(select(Role.id)).all()

    if not roles:
        logger.info("No encontramos roles")
        return

    for _ in range(count):
        role = secrets.choice(roles)

        user = UserFactory.build()
        user.role_id=role
        users.append(user)

    session.add_all(users)
    logger.info(f"{count} usuarios preparados.")
