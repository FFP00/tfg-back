import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.transactionFactory import TransactionFactory
from app.database.models.WalletModel import Wallet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_transactions(session: Session, count: int) -> None:
    wallets = session.exec(select(Wallet.customer_id)).all()

    if not wallets:
        logger.info("No encontramos carteras")
        return

    transactions = []
    for _ in range(count):
        transaction = TransactionFactory.build()
        transaction.customer_id = secrets.choice(wallets)
        transactions.append(transaction)

    session.add_all(transactions)
    logger.info(f"{count} transacciones preparados.")
