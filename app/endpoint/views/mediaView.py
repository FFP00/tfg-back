from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.MediaModel import Media

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
    medias = session.exec(select(Media)).all()
    return templates.TemplateResponse(request, "media/index.html", _ctx(request, medias=medias))


@router.get("/create")
def create(request: Request):
    return templates.TemplateResponse(request, "media/create.html", _ctx(request))


@router.post("/")
def store(
    request: Request,
    path_300x450: str = Form(...),
    path_600x900: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        session.add(Media(path_300x450=path_300x450, path_600x900=path_600x900))
        session.commit()
        return RedirectResponse("/views/media/?success=Media+creado+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "media/create.html",
            _ctx(request, error=str(e), form={"path_300x450": path_300x450, "path_600x900": path_600x900}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    media = session.get(Media, id)
    if not media:
        return RedirectResponse("/views/media/?error=Media+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "media/show.html", _ctx(request, media=media))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    media = session.get(Media, id)
    if not media:
        return RedirectResponse("/views/media/?error=Media+no+encontrado", status_code=302)
    return templates.TemplateResponse(request, "media/edit.html", _ctx(request, media=media))


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    path_300x450: str = Form(...),
    path_600x900: str = Form(...),
    session: Session = Depends(get_session),
):
    media = session.get(Media, id)
    if not media:
        return RedirectResponse("/views/media/?error=Media+no+encontrado", status_code=302)
    try:
        media.path_300x450 = path_300x450
        media.path_600x900 = path_600x900
        session.add(media)
        session.commit()
        return RedirectResponse(f"/views/media/{id}?success=Media+actualizado", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "media/edit.html",
            _ctx(request, media=media, error=str(e)),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    media = session.get(Media, id)
    if not media:
        return RedirectResponse("/views/media/?error=Media+no+encontrado", status_code=302)
    try:
        session.delete(media)
        session.commit()
        return RedirectResponse("/views/media/?success=Media+eliminado", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/media/?error={e}", status_code=302)
