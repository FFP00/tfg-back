import json
import logging
from pathlib import Path

from sqlmodel import Session, select

from app.database.factories.countryFactory import CountryFactory
from app.database.factories.currencyFactory import CurrencyFactory
from app.database.models.CurrencyModel import Currency

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_currencies_countries(session: Session) -> None:
    json_path = Path("/workdir/app/public/data/currencies_countries.json")

    if not json_path.exists():
        logger.error(f"El archivo no existe en la ruta: {json_path}")
        return

    with open(json_path, encoding="utf-8") as file:
        data = json.load(file)

    currencies_unicas = set()
    for entry in data:
        currencies_unicas.add((entry["currency_name"], entry["currency_code"]))

    symbols_map = {entry["currency_code"]: entry.get("currency_symbol", "$") for entry in data}

    currencies = []
    for moneda, codigo in currencies_unicas:
        currency        = CurrencyFactory.build()
        currency.name   = moneda
        currency.code   = codigo
        currency.symbol = symbols_map.get(codigo, "$")
        currencies.append(currency)

    session.add_all(currencies)
    logger.info("Monedas preparadas.")
    session.flush()

    countries = []
    for pais in data:
        currency_id = session.exec(
            select(Currency.id).where(Currency.code == pais["currency_code"])
        ).first()

        if currency_id is None:
            logger.info("No encontramos moneda para el pais")
            return

        country              = CountryFactory.build()
        country.native_name  = pais["official_name"]
        country.english_name = pais["name_en"]
        country.code         = pais["code"]
        country.currency_id  = currency_id
        countries.append(country)

    session.add_all(countries)
    logger.info("Paises preparados.")
