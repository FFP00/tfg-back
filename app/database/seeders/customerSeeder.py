import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.customerFactory import CustomerFactory
from app.database.models.CountryModel import Country
from app.database.models.ImageModel import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_customers(session: Session, count: int) -> None:
    customers = []
    images = session.exec(select(Image.id)).all()
    countries = session.exec(select(Country.id)).all()

    if not images:
        logger.info("No encontramos imagenes")
        return

    if not countries:
        logger.info("No encontramos paises")
        return

    for _ in range(count):
        image = secrets.choice(images)
        country = secrets.choice(countries)

        customer = CustomerFactory.build()
        customer.image_id = image
        customer.country_id = country
        customers.append(customer)

    session.add_all(customers)
    logger.info(f"{count} usuarios preparados.")
