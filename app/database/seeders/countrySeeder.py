import json
import logging
from pathlib import Path

from sqlmodel import Session, select

from app.database.factories.countryFactory import CountryFactory
from app.database.factories.currencyFactory import CurrencyFactory
from app.endpoint.models.CurrencyModel import Currency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_currencies_countries(session: Session):
    json_path = Path("/workdir/app/public/data/currencies_countries.json")

    if not json_path.exists():
        logger.error(f"El archivo no existe en la ruta: {json_path}")
        return

    with open(json_path, encoding="utf-8") as file:
        data = json.load(file)

    currencies_unicas = set()

    for currency in data:

        moneda= currency["currency_name"]
        codigo = currency["currency_code"]

        monedas = (moneda,codigo)

        currencies_unicas.add(monedas)


    currencies = []

    for moneda, codigo in currencies_unicas:

        currency = CurrencyFactory.build()
        currency.name=moneda
        currency.code=codigo
        currencies.append(currency)

    session.add_all(currencies)
    logger.info("Monedas preparadas.")
    session.flush()

    countries = []

    for pais in data:

        country = CountryFactory.build()
        country.name= pais["official_name"]
        country.en_name= pais["name_en"]
        country.code=pais["code"]

        currency_id = session.exec(select(Currency.id).where(Currency.code == pais["currency_code"])).first()

        if currency_id is not None:
            country.currency_id = currency_id

        else:
            logger.info("No encontramos imagenes")
            return

        countries.append(country)

    session.add_all(countries)
    logger.info("Paises preparados.")
