from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.database import get_session
from app.config.errors import human_error
from app.config.templates import templates
from app.database.models.CustomerModel import Customer
from app.database.models.TitleTransactionModel import TitleTransaction
from app.database.models.TransactionModel import Transaction
from app.database.models.UserModel import User

router = APIRouter()

_PAGE = 20


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error":   request.query_params.get("error"),
        **kwargs,
    }


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Transaction)
    count_q = select(func.count()).select_from(Transaction)

    if search:
        matching = session.exec(
            select(Customer.user_id)
            .join(User, Customer.user_id == User.id)
            .where(col(User.name).ilike(f"%{search}%"))
        ).all()
        q       = q.where(col(Transaction.wallet_customer_user_id).in_(matching))
        count_q = count_q.where(col(Transaction.wallet_customer_user_id).in_(matching))

    total        = session.exec(count_q).one()
    transactions = session.exec(
        q.order_by(Transaction.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)
    ).all()

    customer_names: dict[int, str] = {}
    for tx in transactions:
        uid = tx.wallet_customer_user_id
        if uid not in customer_names:
            c = session.get(Customer, uid)
            customer_names[uid] = c.user.name if c and c.user else f"#{uid}"

    return templates.TemplateResponse(request, "transaction/index.html", _ctx(request,
        transactions=transactions, customer_names=customer_names,
        search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transacción+no+encontrada", status_code=302)
    items    = session.exec(
        select(TitleTransaction).where(TitleTransaction.transaction_id == id)
    ).all()
    uid      = transaction.wallet_customer_user_id
    customer = session.get(Customer, uid)
    name     = customer.user.name if customer and customer.user else f"#{uid}"
    return templates.TemplateResponse(request, "transaction/show.html", _ctx(request,
        transaction=transaction, items=items, customer_name=name,
    ))


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transacción+no+encontrada", status_code=302)
    try:
        session.delete(transaction)
        session.commit()
        return RedirectResponse("/views/transaction/?success=Transacción+eliminada", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/transaction/?error={human_error(e)}", status_code=302)
