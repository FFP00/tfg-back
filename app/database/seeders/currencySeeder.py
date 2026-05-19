import logging

from sqlmodel import Session

from app.database.factories.currencyFactory import CurrencyFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_currencies(session: Session, count: int):
    currencies = []

    for _ in range(count):

        currency = CurrencyFactory.build()
        currencies.append(currency)

    session.add_all(currencies)
    logger.info(f"{count} monedas preparados.")
