from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.CountryModel import Country
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


def _get_currencies(session: Session):
    return session.exec(select(Currency)).all()


@router.get("/")
def index(request: Request, search: str = "", session: Session = Depends(get_session)):
    q = select(Country)
    if search:
        q = q.where(
            (Country.name.ilike(f"%{search}%")) | (Country.code.ilike(f"%{search}%"))
        )
    countries = session.exec(q).all()
    return templates.TemplateResponse(request, "country/index.html", _ctx(request, countries=countries, search=search)
    )


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "country/create.html", _ctx(request, currencies=_get_currencies(session))
    )


@router.post("/")
def store(
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    currency_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        cur_id = int(currency_id) if currency_id else None
        session.add(Country(name=name, code=code, currency_id=cur_id))
        session.commit()
        return RedirectResponse("/views/country/?success=Country+creado+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "country/create.html",
            _ctx(request, error=str(e), currencies=_get_currencies(session),
                 form={"name": name, "code": code, "currency_id": currency_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=Country+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "country/show.html", _ctx(request, country=country))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=Country+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "country/edit.html", _ctx(request, country=country, currencies=_get_currencies(session))
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    name: str = Form(...),
    code: str = Form(...),
    currency_id: str = Form(""),
    session: Session = Depends(get_session),
):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=Country+no+encontrado", status_code=302)
    try:
        country.name = name
        country.code = code
        country.currency_id = int(currency_id) if currency_id else None
        session.add(country)
        session.commit()
        return RedirectResponse(f"/views/country/{id}?success=Country+actualizado", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "country/edit.html",
            _ctx(request, country=country, error=str(e), currencies=_get_currencies(session),
                 form={"name": name, "code": code, "currency_id": currency_id}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    country = session.get(Country, id)
    if not country:
        return RedirectResponse("/views/country/?error=Country+no+encontrado", status_code=302)
    try:
        session.delete(country)
        session.commit()
        return RedirectResponse("/views/country/?success=Country+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/country/?error={e}", status_code=302)
