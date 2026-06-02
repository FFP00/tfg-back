import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.titleTransactionFactory import TitleTransactionFactory
from app.database.models.TitleModel import Title
from app.database.models.TransactionModel import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_titles_transactions(session: Session, count: int) -> None:
    titles_transactions = []
    titles = [t for t in session.exec(select(Title.id)).all() if t is not None]
    transactions = [
        t for t in session.exec(select(Transaction.id)).all() if t is not None
    ]

    if not titles:
        logger.info("No encontramos juegos")
        return

    if not transactions:
        logger.info("No encontramos transacciones")
        return

    used = set()
    attempts = 0
    max_attempts = count * 10

    while len(titles_transactions) < count and attempts < max_attempts:
        attempts += 1
        title = secrets.choice(titles)
        transaction = secrets.choice(transactions)

        if (title, transaction) in used:
            continue

        used.add((title, transaction))
        title_transaction = TitleTransactionFactory.build()
        title_transaction.title_id = title
        title_transaction.transaction_id = transaction
        titles_transactions.append(title_transaction)

    session.add_all(titles_transactions)
    logger.info(f"{count} title_transaction preparados.")
