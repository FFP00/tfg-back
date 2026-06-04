import logging
import secrets

from sqlmodel import Session, select

from app.database.factories.titleTransactionFactory import TitleTransactionFactory
from app.database.models.TitleModel import Title
from app.database.models.TransactionModel import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_titles_transactions(session: Session, count: int) -> None:
    titles       = session.exec(select(Title)).all()
    transactions = session.exec(select(Transaction.id)).all()

    if not titles:
        logger.info("No encontramos juegos")
        return

    if not transactions:
        logger.info("No encontramos transacciones")
        return

    used: set[tuple[int, int]] = set()
    records = []

    while len(records) < count:
        title          = secrets.choice(titles)
        transaction_id = secrets.choice(transactions)

        if (title.id, transaction_id) in used:
            continue

        used.add((title.id, transaction_id))

        tt                = TitleTransactionFactory.build()
        tt.title_id       = title.id
        tt.transaction_id = transaction_id
        tt.price          = title.release_price
        tt.discount       = 0 if title.release_price == 0 else tt.discount
        records.append(tt)

    session.add_all(records)
    logger.info(f"{count} title_transaction preparados.")
