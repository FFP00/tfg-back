from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import func
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.DeveloperModel import Developer
from app.database.models.MediaModel import Media
from app.database.models.TitleModel import Title

_PAGE         = 20
_PHOTO_FIELDS = ("capsule", "header", "store_1", "store_2", "store_3", "store_4", "store_5", "store_6")

router = APIRouter()


def _ctx(request: Request, **kwargs):
    return {
        "request": request,
        "success": request.query_params.get("success"),
        "error":   request.query_params.get("error"),
        "form":    {},
        **kwargs,
    }


def _developers(session: Session):
    return session.exec(select(Developer)).all()



@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Title)
    count_q = select(func.count()).select_from(Title)
    if search:
        cond    = Title.name.ilike(f"%{search}%")
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total  = session.exec(count_q).one()
    titles = session.exec(q.offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "title/index.html", _ctx(request,
        titles=titles, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(request, "title/create.html",
        _ctx(request, developers=_developers(session)),
    )


@router.post("/")
def store(
    request:         Request,
    name:            str     = Form(...),
    status:          str     = Form("true"),
    actual_discount: int     = Form(0),
    release_date:    str     = Form(...),
    release_price:   str     = Form(...),
    developer_id:    str     = Form(""),
    session:         Session = Depends(get_session),
):
    try:
        session.add(Title(
            name=name,
            status=status == "true",
            actual_discount=actual_discount,
            release_date=date.fromisoformat(release_date),
            release_price=Decimal(release_price),
            developer_id=int(developer_id) if developer_id else None,
        ))
        session.commit()
        return RedirectResponse("/views/title/?success=Title+creado+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "title/create.html",
            _ctx(request, error=str(e), developers=_developers(session),
                 form={"name": name, "status": status == "true", "actual_discount": actual_discount,
                       "release_date": release_date, "release_price": release_price,
                       "developer_id": developer_id}),
        )


@router.get("/{id}/media/{field}")
def get_media(id: int, field: str, session: Session = Depends(get_session)) -> Response:
    if field not in (*_PHOTO_FIELDS, "trailer"):
        raise HTTPException(status_code=400, detail="Campo inválido")
    title = session.get(Title, id)
    if not title:
        raise HTTPException(status_code=404, detail="Media no encontrada")
    media = session.exec(select(Media).where(Media.title_id == id)).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media no encontrada")
    data: bytes | None = getattr(media, field, None)
    if not data:
        raise HTTPException(status_code=404, detail=f"Campo '{field}' vacío")
    media_type = "video/mp4" if field == "trailer" else "image/jpeg"
    return Response(content=data, media_type=media_type)


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    media        = session.exec(select(Media).where(Media.title_id == id)).first()
    photo_fields = [f for f in _PHOTO_FIELDS if media and getattr(media, f)]
    has_trailer  = bool(media and media.trailer)
    return templates.TemplateResponse(request, "title/show.html", _ctx(request,
        title=title, photo_fields=photo_fields, has_trailer=has_trailer,
    ))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "title/edit.html",
        _ctx(request, title=title, developers=_developers(session)),
    )


@router.post("/{id}/update")
def update(
    id:              int,
    request:         Request,
    name:            str     = Form(...),
    status:          str     = Form("true"),
    actual_discount: int     = Form(0),
    release_date:    str     = Form(...),
    release_price:   str     = Form(...),
    developer_id:    str     = Form(""),
    session:         Session = Depends(get_session),
):
    title = session.get(Title, id)
    if not title:
        return RedirectResponse("/views/title/?error=Title+no+encontrado", status_code=302)
    try:
        title.name            = name
        title.status          = status == "true"
        title.actual_discount = actual_discount
        title.release_date    = date.fromisoformat(release_date)
        title.release_price   = Decimal(release_price)
        title.developer_id    = int(developer_id) if developer_id else None
        session.add(title)
        session.commit()
        return RedirectResponse(f"/views/title/{id}?success=Title+actualizado", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "title/edit.html",
            _ctx(request, title=title, error=str(e),
                 developers=_developers(session)),
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
