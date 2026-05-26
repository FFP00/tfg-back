from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.DeveloperModel import Developer
from app.endpoint.models.MediaModel import Media
from app.endpoint.models.TitleModel import Title

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
        session.exec(select(Developer)).all(),
        session.exec(select(Media)).all(),
    )


@router.get("/")
def index(request: Request, search: str = "", session: Session = Depends(get_session)):
    q = select(Title)
    if search:
        q = q.where(Title.name.ilike(f"%{search}%"))
    titles = session.exec(q).all()
    return templates.TemplateResponse(request, "title/index.html", _ctx(request, titles=titles, search=search)
    )


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    developers, medias = _get_deps(session)
    return templates.TemplateResponse(request, "title/create.html", _ctx(request, developers=developers, medias=medias)
    )


@router.post("/")
def store(
    request: Request,
    name: str = Form(...),
    status: str = Form("true"),
    actual_discount: int = Form(0),
    release_date: str = Form(...),
    release_price: str = Form(...),
    developer_id: str = Form(""),
    media_id: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        session.add(Title(
            name=name,
            status=status == "true",
            actual_discount=actual_discount,
            release_date=date.fromisoformat(release_date),
            release_price=Decimal(release_price),
            developer_id=int(developer_id) if developer_id else None,
            media_id=int(media_id) if media_id else None,
        ))
        session.commit()
        return RedirectResponse("/views/title/?success=Title+creado+correctamente", status_code=302)
    except Exception as e:
        developers, medias = _get_deps(session)
        return templates.TemplateResponse(request, "title/create.html",
            _ctx(request, error=str(e), developers=developers, medias=medias,
                 form={"name": name, "status": status == "true", "actual_discount": actual_discount,
                       "release_date": release_date, "release_price": release_price,
                       "developer_id": developer_id, "media_id": media_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "title/show.html", _ctx(request, title=title))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    developers, medias = _get_deps(session)
    return templates.TemplateResponse(request, "title/edit.html", _ctx(request, title=title, developers=developers, medias=medias)
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    name: str = Form(...),
    status: str = Form("true"),
    actual_discount: int = Form(0),
    release_date: str = Form(...),
    release_price: str = Form(...),
    developer_id: str = Form(""),
    media_id: str = Form(""),
    session: Session = Depends(get_session),
):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    try:
        title.name = name
        title.status = status == "true"
        title.actual_discount = actual_discount
        title.release_date = date.fromisoformat(release_date)
        title.release_price = Decimal(release_price)
        title.developer_id = int(developer_id) if developer_id else None
        title.media_id = int(media_id) if media_id else None
        session.add(title)
        session.commit()
        return RedirectResponse(f"/views/title/{id}?success=Title+actualizado", status_code=302)
    except Exception as e:
        developers, medias = _get_deps(session)
        return templates.TemplateResponse(request, "title/edit.html",
            _ctx(request, title=title, error=str(e), developers=developers, medias=medias),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    try:
        session.delete(title)
        session.commit()
        return RedirectResponse("/views/title/?success=Title+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/title/?error={e}", status_code=302)
