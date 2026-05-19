import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.transactionFactory import TransactionFactory
from app.endpoint.models.WalletModel import Wallet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_transactions(session: Session, count: int):
    transactions = []
    wallets = session.exec(select(Wallet.customer_id)).all()

    if not wallets:
        logger.info("No encontramos carteras")
        return

    for _ in range(count):
        wallet = secrets.choice(wallets)

        transaction = TransactionFactory.build()
        transaction.wallet_customer_id=wallet
        transactions.append(transaction)

    session.add_all(transactions)
    logger.info(f"{count} transacciones preparados.")
