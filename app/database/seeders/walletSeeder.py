import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.walletFactory import WalletFactory
from app.endpoint.models.CustomerModel import Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_wallets(session: Session, count: int):
    wallets = []
    customers = list(session.exec(select(Customer.id)).all())

    if not customers:
        logger.info("No encontramos usuarios")
        return

    for _ in range(count):
        customer = secrets.randbelow(len(customers))
        selected_customer = customers.pop(customer)

        wallet = WalletFactory.build()
        wallet.customer_id=selected_customer
        wallets.append(wallet)

    session.add_all(wallets)
    logger.info(f"{count} carteras preparados.")
