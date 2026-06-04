from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from pwdlib import PasswordHash
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.config.database import get_session
from app.config.errors import human_error
from app.config.templates import templates
from app.database.models.CountryModel import Country
from app.database.models.DeveloperModel import Developer
from app.database.models.UserModel import User

hasher = PasswordHash.recommended()

_PAGE = 20

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error":   request.query_params.get("error"),
        "form":    {},
        **kwargs,
    }


def _countries(session: Session):
    return session.exec(select(Country).order_by(Country.english_name)).all()


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Developer).join(User, Developer.user_id == User.id)
    count_q = select(func.count()).select_from(Developer).join(User, Developer.user_id == User.id)
    if search:
        cond    = (
            col(User.name).ilike(f"%{search}%")
            | col(Developer.support_email).ilike(f"%{search}%")
            | col(Developer.website_url).ilike(f"%{search}%")
        )
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total      = session.exec(count_q).one()
    developers = session.exec(q.order_by(Developer.created_at.desc()).offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "developer/index.html", _ctx(request,
        developers=developers, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "developer/create.html", _ctx(request, countries=_countries(session)))


@router.post("/")
def store(
    request:       Request,
    name:          str     = Form(...),
    email:         str     = Form(...),
    support_email: str     = Form(...),
    password:      str     = Form(...),
    website_url:   str     = Form(""),
    country_id:    str     = Form(""),
    status:        str     = Form("false"),
    session:       Session = Depends(get_session),
):
    try:
        user = User(
            name       = name,
            email      = email,
            password   = hasher.hash(password),
            country_id = int(country_id) if country_id else None,
            type       = "DEV",
        )
        session.add(user)
        session.flush()
        session.add(Developer(
            user_id       = user.id,
            support_email = support_email,
            website_url   = website_url or None,
            status        = status == "true",
        ))
        session.commit()
        return RedirectResponse("/views/developer/?success=Developer+creado+correctamente", status_code=302)
    except Exception as e:
        session.rollback()
        return templates.TemplateResponse(request, "developer/create.html",
            _ctx(request, error=human_error(e), countries=_countries(session),
                 form={"name": name, "email": email, "support_email": support_email,
                       "website_url": website_url, "country_id": country_id, "status": status == "true"}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    developer = session.get(Developer, id)
    if not developer:
        return RedirectResponse("/views/developer/?error=Developer+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "developer/show.html", _ctx(request, developer=developer))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    developer = session.get(Developer, id)
    if not developer:
        return RedirectResponse("/views/developer/?error=Developer+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "developer/edit.html",
        _ctx(request, developer=developer, countries=_countries(session)),
    )


@router.post("/{id}/update")
def update(
    id:            int,
    request:       Request,
    name:          str     = Form(...),
    email:         str     = Form(...),
    support_email: str     = Form(...),
    password:      str     = Form(""),
    website_url:   str     = Form(""),
    country_id:    str     = Form(""),
    status:        str     = Form("false"),
    session:       Session = Depends(get_session),
):
    developer = session.get(Developer, id)
    if not developer:
        return RedirectResponse("/views/developer/?error=Developer+no+encontrado", status_code=302)
    try:
        user            = developer.user
        user.name       = name
        user.email      = email
        user.country_id = int(country_id) if country_id else None
        if password:
            user.password = hasher.hash(password)
        session.add(user)

        developer.support_email = support_email
        developer.website_url   = website_url or None
        developer.status        = status == "true"
        session.add(developer)
        session.commit()
        return RedirectResponse(f"/views/developer/{id}?success=Developer+actualizado", status_code=302)
    except Exception as e:
        session.rollback()
        developer = session.get(Developer, id)
        return templates.TemplateResponse(request, "developer/edit.html",
            _ctx(request, developer=developer, error=human_error(e), countries=_countries(session),
                 form={"name": name, "email": email, "support_email": support_email,
                       "website_url": website_url, "country_id": country_id, "status": status == "true"}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    developer = session.get(Developer, id)
    if not developer:
        return RedirectResponse("/views/developer/?error=Developer+no+encontrado", status_code=302)
    try:
        user = developer.user
        session.delete(developer)
        session.flush()
        if user:
            session.delete(user)
        session.commit()
        return RedirectResponse("/views/developer/?success=Developer+eliminado", status_code=302)
    except Exception as e:
        session.rollback()
        return RedirectResponse(f"/views/developer/?error={human_error(e)}", status_code=302)
