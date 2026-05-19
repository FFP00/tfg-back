import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.countryFactory import CountryFactory
from app.endpoint.models.CurrencyModel import Currency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_countries(session: Session, count: int):
    countries = []
    currencies = session.exec(select(Currency.id)).all()

    if not currencies:
        logger.info("No encontramos monedas")
        return

    for _ in range(count):
        currency = secrets.choice(currencies)
        country = CountryFactory.build()

        country.currency_id=currency
        countries.append(country)

    session.add_all(countries)
    logger.info(f"{count} paises preparados.")
