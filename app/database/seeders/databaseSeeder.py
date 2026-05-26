import logging

from sqlmodel import Session

from app.config.database import engine
from app.database.seeders.countrySeeder import seed_currencies_countries
from app.database.seeders.customerSeeder import seed_customers
from app.database.seeders.customerTitleSeeder import seed_customers_titles
from app.database.seeders.developerSeeder import seed_developers
from app.database.seeders.friendshipSeeder import seed_friendships
from app.database.seeders.genreSeeder import seed_genres
from app.database.seeders.genreTitleSeeder import seed_genres_titles
from app.database.seeders.imageSeeder import seed_images
from app.database.seeders.mediaSeeder import seed_medias
from app.database.seeders.reviewSeeder import seed_reviews
from app.database.seeders.titleSeeder import seed_titles
from app.database.seeders.titleTransactionSeeder import seed_titles_transactions
from app.database.seeders.transactionSeeder import seed_transactions
from app.database.seeders.walletSeeder import seed_wallets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_seed():

    logger.info("Iniciando databaseSeeder.py")
    with Session(engine) as session:
        try:

            seed_currencies_countries   (session)
            seed_images                 (session, count=150)
            seed_medias                 (session, count=150)
            seed_genres                 (session, count=15)
            seed_developers             (session, count=150)
            seed_customers              (session, count=150)
            seed_titles                 (session, count=150)
            seed_wallets                (session, count=150)
            seed_friendships            (session, count=300)
            seed_genres_titles          (session, count=15)
            seed_customers_titles       (session, count=300)
            seed_transactions           (session, count=500)
            seed_reviews                (session, count=500)
            seed_titles_transactions    (session, count=500)
            session.commit()

        except Exception as e:
            logger.error(e)
            session.rollback()
            raise e

if __name__ == "__main__":
    run_seed()
