from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.TitleModel import Title
from app.endpoint.models.TitleTransactionModel import TitleTransaction
from app.endpoint.models.TransactionModel import Transaction

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


def _get_deps(session: Session):
    return (
        session.exec(select(Title)).all(),
        session.exec(select(Transaction)).all(),
    )


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    title_transactions = session.exec(select(TitleTransaction)).all()
    return templates.TemplateResponse(request, "title_transaction/index.html", _ctx(request, title_transactions=title_transactions)
    )


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    titles, transactions = _get_deps(session)
    return templates.TemplateResponse(request, "title_transaction/create.html", _ctx(request, titles=titles, transactions=transactions)
    )


@router.post("/")
def store(
    request: Request,
    price: str = Form(...),
    discount: int = Form(0),
    title_id: str = Form(""),
    transaction_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        session.add(TitleTransaction(
            price=Decimal(price),
            discount=discount,
            title_id=int(title_id) if title_id else None,
            transaction_id=int(transaction_id) if transaction_id else None,
        ))
        session.commit()
        return RedirectResponse(
            "/views/title_transaction/?success=Title-Transaction+creado+correctamente", status_code=302
        )
    except Exception as e:
        titles, transactions = _get_deps(session)
        return templates.TemplateResponse(request, "title_transaction/create.html",
            _ctx(request, error=str(e), titles=titles, transactions=transactions,
                 form={"price": price, "discount": discount,
                       "title_id": title_id, "transaction_id": transaction_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    title_transaction = session.get(TitleTransaction, id)
    if not title_transaction:
        return RedirectResponse(
            "/views/title_transaction/?error=Title-Transaction+no+encontrado", status_code=302
        )
    return templates.TemplateResponse(request, "title_transaction/show.html", _ctx(request, title_transaction=title_transaction)
    )


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    title_transaction = session.get(TitleTransaction, id)
    if not title_transaction:
        return RedirectResponse(
            "/views/title_transaction/?error=Title-Transaction+no+encontrado", status_code=302
        )
    titles, transactions = _get_deps(session)
    return templates.TemplateResponse(request, "title_transaction/edit.html",
        _ctx(request, title_transaction=title_transaction, titles=titles, transactions=transactions),
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    price: str = Form(...),
    discount: int = Form(0),
    title_id: str = Form(""),
    transaction_id: str = Form(""),
    session: Session = Depends(get_session),
):
    title_transaction = session.get(TitleTransaction, id)
    if not title_transaction:
        return RedirectResponse(
            "/views/title_transaction/?error=Title-Transaction+no+encontrado", status_code=302
        )
    try:
        title_transaction.price = Decimal(price)
        title_transaction.discount = discount
        title_transaction.title_id = int(title_id) if title_id else None
        title_transaction.transaction_id = int(transaction_id) if transaction_id else None
        session.add(title_transaction)
        session.commit()
        return RedirectResponse(
            f"/views/title_transaction/{id}?success=Title-Transaction+actualizado", status_code=302
        )
    except Exception as e:
        titles, transactions = _get_deps(session)
        return templates.TemplateResponse(request, "title_transaction/edit.html",
            _ctx(request, title_transaction=title_transaction, error=str(e),
                 titles=titles, transactions=transactions),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    title_transaction = session.get(TitleTransaction, id)
    if not title_transaction:
        return RedirectResponse(
            "/views/title_transaction/?error=Title-Transaction+no+encontrado", status_code=302
        )
    try:
        session.delete(title_transaction)
        session.commit()
        return RedirectResponse(
            "/views/title_transaction/?success=Title-Transaction+eliminado", status_code=302
        )
    except Exception as e:
        return RedirectResponse(f"/views/title_transaction/?error={e}", status_code=302)
