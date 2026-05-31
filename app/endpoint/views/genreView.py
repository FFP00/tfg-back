from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.database.models.GenreModel import Genre

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


@router.get("/")
def index(request: Request, search: str = "", page: int = 1, session: Session = Depends(get_session)):
    q       = select(Genre)
    count_q = select(func.count()).select_from(Genre)
    if search:
        cond    = Genre.name.ilike(f"%{search}%")
        q       = q.where(cond)
        count_q = count_q.where(cond)
    total  = session.exec(count_q).one()
    genres = session.exec(q.offset((page - 1) * _PAGE).limit(_PAGE)).all()
    return templates.TemplateResponse(request, "genre/index.html", _ctx(request,
        genres=genres, search=search, page=page,
        has_prev=page > 1, has_next=(page * _PAGE) < total,
    ))


@router.get("/create")
def create(request: Request):
    return templates.TemplateResponse(request, "genre/create.html", _ctx(request))


@router.post("/")
def store(
    request: Request,
    name: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        session.add(Genre(name=name))
        session.commit()
        return RedirectResponse("/views/genre/?success=Genre+creado+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "genre/create.html",
            _ctx(request, error=str(e), form={"name": name}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    genre = session.get(Genre, id)
    if not genre:
        return RedirectResponse("/views/genre/?error=Genre+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "genre/show.html", _ctx(request, genre=genre))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    genre = session.get(Genre, id)
    if not genre:
        return RedirectResponse("/views/genre/?error=Genre+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "genre/edit.html", _ctx(request, genre=genre))


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    name: str = Form(...),
    session: Session = Depends(get_session),
):
    genre = session.get(Genre, id)
    if not genre:
        return RedirectResponse("/views/genre/?error=Genre+no+encontrado", status_code=302)
    try:
        genre.name = name
        session.add(genre)
        session.commit()
        return RedirectResponse(f"/views/genre/{id}?success=Genre+actualizado", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "genre/edit.html",
            _ctx(request, genre=genre, error=str(e), form={"name": name}),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    genre = session.get(Genre, id)
    if not genre:
        return RedirectResponse("/views/genre/?error=Genre+no+encontrado", status_code=302)
    try:
        session.delete(genre)
        session.commit()
        return RedirectResponse("/views/genre/?success=Genre+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/genre/?error={e}", status_code=302)
