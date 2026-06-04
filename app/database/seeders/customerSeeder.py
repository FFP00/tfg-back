import logging
import secrets
from decimal import Decimal

from sqlmodel import Session, select

from app.database.factories.customerFactory import CustomerFactory
from app.database.factories.userFactory import UserFactory
from app.database.models.CountryModel import Country
from app.database.models.WalletModel import Wallet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_BALANCES = list(range(0, 65, 5))


def seed_customers(session: Session, count: int) -> None:
    countries = session.exec(select(Country.id)).all()

    if not countries:
        logger.info("No encontramos paises")
        return

    users = []
    for _ in range(count):
        user            = UserFactory.build()
        user.type       = "CUS"
        user.country_id = secrets.choice(countries)
        session.add(user)
        users.append(user)

    session.flush()

    customers = []
    for user in users:
        customers.append(CustomerFactory.build(user_id=user.id))

    session.add_all(customers)
    session.flush()

    for user in users:
        wallet         = session.get(Wallet, user.id)
        wallet.balance = Decimal(str(secrets.choice(_BALANCES)))

    logger.info(f"{count} customers preparados.")
