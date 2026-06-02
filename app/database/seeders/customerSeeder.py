import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.customerFactory import CustomerFactory
from app.database.models.CountryModel import Country

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_customers(session: Session, count: int) -> None:
    countries = session.exec(select(Country.id)).all()

    if not countries:
        logger.info("No encontramos paises")
        return

    customers = []
    for _ in range(count):
        customer = CustomerFactory.build()
        customer.country_id = secrets.choice(countries)
        customers.append(customer)

    session.add_all(customers)
    logger.info(f"{count} usuarios preparados.")
