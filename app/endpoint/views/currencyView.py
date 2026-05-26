from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CurrencyModel import Currency

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


# ── Index ────────────────────────────────────────────────────────────────────

@router.get("/")
def index(request: Request, search: str = "", session: Session = Depends(get_session)):
    q = select(Currency)
    if search:
        q = q.where(
            (Currency.name.ilike(f"%{search}%")) | (Currency.code.ilike(f"%{search}%"))
        )
    currencies = session.exec(q).all()
    return templates.TemplateResponse(request, "currency/index.html", _ctx(request, currencies=currencies, search=search)
    )


# ── Create ───────────────────────────────────────────────────────────────────

@router.get("/create")
def create(request: Request):
    return templates.TemplateResponse(request, "currency/create.html", _ctx(request))


@router.post("/")
def store(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        session.add(Currency(name=name, code=code))
        session.commit()
        return RedirectResponse("/views/currency/?success=Currency+creada+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "currency/create.html",
            _ctx(request, error=str(e), form={"name": name, "code": code}),
        )


# ── Show ─────────────────────────────────────────────────────────────────────

@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Currency+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "currency/show.html", _ctx(request, currency=currency))


# ── Edit ─────────────────────────────────────────────────────────────────────

@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Currency+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "currency/edit.html", _ctx(request, currency=currency))


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    session: Session = Depends(get_session),
):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Currency+no+encontrada", status_code=302)
    try:
        currency.name = name
        currency.code = code
        session.add(currency)
        session.commit()
        return RedirectResponse(f"/views/currency/{id}?success=Currency+actualizada", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "currency/edit.html",
            _ctx(request, currency=currency, error=str(e), form={"name": name, "code": code}),
        )


# ── Delete ───────────────────────────────────────────────────────────────────

@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    currency = session.get(Currency, id)
    if not currency:
        return RedirectResponse("/views/currency/?error=Currency+no+encontrada", status_code=302)
    try:
        session.delete(currency)
        session.commit()
        return RedirectResponse("/views/currency/?success=Currency+eliminada", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/currency/?error={e}", status_code=302)
