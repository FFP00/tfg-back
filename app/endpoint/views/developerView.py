from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.DeveloperModel import Developer
from app.database.models.ImageModel import Image

_PAGE = 20

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "form": {},
        **kwargs,
    }


def _get_images(session: Session):
    return session.exec(select(Image)).all()


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Developer)
    count_q = select(func.count()).select_from(Developer)
    if search:
        cond    = (Developer.name.ilike(f"%{search}%")) | (Developer.email.ilike(f"%{search}%"))
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total      = session.exec(count_q).one()
    developers = session.exec(q.offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "developer/index.html", _ctx(request,
        developers=developers, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "developer/create.html", _ctx(request, images=_get_images(session))
    )


@router.post("/")
def store(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    support_email: str = Form(...),
    password: str = Form(...),
    website_url: str = Form(""),
    status: str = Form("true"),
    image_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        session.add(Developer(
            name=name,
            email=email,
            support_email=support_email,
            password=password,
            website_url=website_url or None,
            status=status == "true",
            image_id=int(image_id) if image_id else None,
        ))
        session.commit()
        return RedirectResponse("/views/developer/?success=Developer+creado+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "developer/create.html",
            _ctx(request, error=str(e), images=_get_images(session),
                 form={"name": name, "email": email, "support_email": support_email,
                       "website_url": website_url, "status": status == "true", "image_id": image_id}),
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
    return templates.TemplateResponse(request, "developer/edit.html", _ctx(request, developer=developer, images=_get_images(session))
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    support_email: str = Form(...),
    password: str = Form(""),
    website_url: str = Form(""),
    status: str = Form("true"),
    image_id: str = Form(""),
    session: Session = Depends(get_session),
):
    developer = session.get(Developer, id)
    if not developer:
        return RedirectResponse("/views/developer/?error=Developer+no+encontrado", status_code=302)
    try:
        developer.name = name
        developer.email = email
        developer.support_email = support_email
        if password:
            developer.password = password
        developer.website_url = website_url or None
        developer.status = status == "true"
        developer.image_id = int(image_id) if image_id else None
        session.add(developer)
        session.commit()
        return RedirectResponse(f"/views/developer/{id}?success=Developer+actualizado", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "developer/edit.html",
            _ctx(request, developer=developer, error=str(e), images=_get_images(session)),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    developer = session.get(Developer, id)
    if not developer:
        return RedirectResponse("/views/developer/?error=Developer+no+encontrado", status_code=302)
    try:
        session.delete(developer)
        session.commit()
        return RedirectResponse("/views/developer/?success=Developer+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/developer/?error={e}", status_code=302)
