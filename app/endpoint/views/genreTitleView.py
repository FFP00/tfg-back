from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.GenreModel import Genre
from app.endpoint.models.GenreTitleModel import GenreTitle
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
        session.exec(select(Title)).all(),
        session.exec(select(Genre)).all(),
    )


@router.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    genre_titles = session.exec(select(GenreTitle)).all()
    return templates.TemplateResponse(request, "genre_title/index.html", _ctx(request, genre_titles=genre_titles))


@router.get("/create")
def create(request: Request, session: Session = Depends(get_session)):
    titles, genres = _get_deps(session)
    return templates.TemplateResponse(request, "genre_title/create.html", _ctx(request, titles=titles, genres=genres)
    )


@router.post("/")
def store(
    request: Request,
    title_id: str = Form(...),
    genre_id: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        session.add(GenreTitle(
            title_id=int(title_id),
            genre_id=int(genre_id),
        ))
        session.commit()
        return RedirectResponse("/views/genre_title/?success=Genre-Title+creado+correctamente", status_code=302)
    except Exception as e:
        titles, genres = _get_deps(session)
        return templates.TemplateResponse(request, "genre_title/create.html",
            _ctx(request, error=str(e), titles=titles, genres=genres,
                 form={"title_id": title_id, "genre_id": genre_id}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    genre_title = session.get(GenreTitle, id)
    if not genre_title:
        return RedirectResponse("/views/genre_title/?error=Genre-Title+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "genre_title/show.html", _ctx(request, genre_title=genre_title))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    genre_title = session.get(GenreTitle, id)
    if not genre_title:
        return RedirectResponse("/views/genre_title/?error=Genre-Title+no+encontrado", status_code=302)
    titles, genres = _get_deps(session)
    return templates.TemplateResponse(request, "genre_title/edit.html", _ctx(request, genre_title=genre_title, titles=titles, genres=genres)
    )


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    title_id: str = Form(...),
    genre_id: str = Form(...),
    session: Session = Depends(get_session),
):
    genre_title = session.get(GenreTitle, id)
    if not genre_title:
        return RedirectResponse("/views/genre_title/?error=Genre-Title+no+encontrado", status_code=302)
    try:
        genre_title.title_id = int(title_id)
        genre_title.genre_id = int(genre_id)
        session.add(genre_title)
        session.commit()
        return RedirectResponse(f"/views/genre_title/{id}?success=Genre-Title+actualizado", status_code=302)
    except Exception as e:
        titles, genres = _get_deps(session)
        return templates.TemplateResponse(request, "genre_title/edit.html",
            _ctx(request, genre_title=genre_title, error=str(e), titles=titles, genres=genres),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    genre_title = session.get(GenreTitle, id)
    if not genre_title:
        return RedirectResponse("/views/genre_title/?error=Genre-Title+no+encontrado", status_code=302)
    try:
        session.delete(genre_title)
        session.commit()
        return RedirectResponse("/views/genre_title/?success=Genre-Title+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/genre_title/?error={e}", status_code=302)
