from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.TransactionModel import Transaction

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
def index(request: Request, page: int = 1, session: Session = Depends(get_session)):
    total        = session.exec(select(func.count()).select_from(Transaction)).one()
    transactions = session.exec(select(Transaction).offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "transaction/index.html", _ctx(request,
        transactions=transactions, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transaction+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "transaction/show.html", _ctx(request, transaction=transaction))


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transaction+no+encontrada", status_code=302)
    try:
        session.delete(transaction)
        session.commit()
        return RedirectResponse("/views/transaction/?success=Transaction+eliminada", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/transaction/?error={e}", status_code=302)
