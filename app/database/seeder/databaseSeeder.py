import logging

from sqlmodel import Session

from app.database.seeder.roleSeeder import seed_roles
from app.database.seeder.userSeeder import seed_users
from app.settings.connection import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_seed():

    logger.info("Iniciando DatabaseSeeder...")
    with Session(engine) as session:
        try:

            seed_roles(session)
            seed_users(session, count=150)
            session.commit()

        except Exception as e:
            logger.error(e)
            session.rollback()
            raise e

if __name__ == "__main__":
    run_seed()
