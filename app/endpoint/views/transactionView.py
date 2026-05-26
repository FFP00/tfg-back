from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.TransactionModel import Transaction
from app.endpoint.models.WalletModel import Wallet

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    transactions = session.exec(select(Transaction)).all()
    return templates.TemplateResponse(request, "transaction/index.html", _ctx(request, transactions=transactions)
    )


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    wallets = session.exec(select(Wallet)).all()
    return templates.TemplateResponse(request, "transaction/create.html", _ctx(request, wallets=wallets))


@router.post("/")
def store(
    request: Request,
    wallet_customer_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        session.add(Transaction(
            wallet_customer_id=int(wallet_customer_id) if wallet_customer_id else None,
        ))
        session.commit()
        return RedirectResponse(
            "/views/transaction/?success=Transaction+creada+correctamente", status_code=302
        )
    except Exception as e:
        wallets = session.exec(select(Wallet)).all()
        return templates.TemplateResponse(request, "transaction/create.html",
            _ctx(request, error=str(e), wallets=wallets,
                 form={"wallet_customer_id": wallet_customer_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transaction+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "transaction/show.html", _ctx(request, transaction=transaction)
    )


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transaction+no+encontrada", status_code=302)
    wallets = session.exec(select(Wallet)).all()
    return templates.TemplateResponse(request, "transaction/edit.html", _ctx(request, transaction=transaction, wallets=wallets)
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    wallet_customer_id: str = Form(""),
    session: Session = Depends(get_session),
):
    transaction = session.get(Transaction, id)
    if not transaction:
        return RedirectResponse("/views/transaction/?error=Transaction+no+encontrada", status_code=302)
    try:
        transaction.wallet_customer_id = int(wallet_customer_id) if wallet_customer_id else None
        session.add(transaction)
        session.commit()
        return RedirectResponse(
            f"/views/transaction/{id}?success=Transaction+actualizada", status_code=302
        )
    except Exception as e:
        wallets = session.exec(select(Wallet)).all()
        return templates.TemplateResponse(request, "transaction/edit.html",
            _ctx(request, transaction=transaction, error=str(e), wallets=wallets),
        )


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
