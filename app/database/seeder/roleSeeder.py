import logging

from sqlmodel import Session

from app.database.factory.roleFactory import RoleFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_roles(session: Session):

    roles = RoleFactory.batch(3)

    session.add_all(roles)
