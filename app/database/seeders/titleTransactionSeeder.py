import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.titleTransactionFactory import TitleTransactionFactory
from app.endpoint.models.TitleModel import Title
from app.endpoint.models.TransactionModel import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_titles_transactions(session: Session, count: int):
    titles_transactions = []
    titles = session.exec(select(Title.id)).all()
    transactions = session.exec(select(Transaction.id)).all()


    if not titles:
        logger.info("No encontramos juegos")
        return

    if not transactions:
        logger.info("No encontramos transacciones")
        return

    for _ in range(count):
        title = secrets.choice(titles)
        transaction = secrets.choice(transactions)

        title_transaction = TitleTransactionFactory.build()
        title_transaction.title_id=title
        title_transaction.transaction_id = transaction
        titles_transactions.append(title_transaction)

    session.add_all(titles_transactions)
    logger.info(f"{count} title_transaction preparados.")
