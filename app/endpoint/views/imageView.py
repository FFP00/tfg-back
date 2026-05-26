from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from app.config.database import get_session
from app.config.templates import templates
from app.endpoint.models.ImageModel import Image

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
    images = session.exec(select(Image)).all()
    return templates.TemplateResponse(request, "image/index.html", _ctx(request, images=images))


@router.get("/create")
def create(request: Request):
    return templates.TemplateResponse(request, "image/create.html", _ctx(request))


@router.post("/")
def store(
    request: Request,
    path_256x256: str = Form(...),
    path_512x512: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        session.add(Image(path_256x256=path_256x256, path_512x512=path_512x512))
        session.commit()
        return RedirectResponse("/views/image/?success=Image+creada+correctamente", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "image/create.html",
            _ctx(request, error=str(e), form={"path_256x256": path_256x256, "path_512x512": path_512x512}),
        )


@router.get("/{id}")
def show(id: int, request: Request, session: Session = Depends(get_session)):
    image = session.get(Image, id)
    if not image:
        return RedirectResponse("/views/image/?error=Image+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "image/show.html", _ctx(request, image=image))


@router.get("/{id}/edit")
def edit(id: int, request: Request, session: Session = Depends(get_session)):
    image = session.get(Image, id)
    if not image:
        return RedirectResponse("/views/image/?error=Image+no+encontrada", status_code=302)
    return templates.TemplateResponse(request, "image/edit.html", _ctx(request, image=image))


@router.post("/{id}/update")
def update(
    id: int,
    request: Request,
    path_256x256: str = Form(...),
    path_512x512: str = Form(...),
    session: Session = Depends(get_session),
):
    image = session.get(Image, id)
    if not image:
        return RedirectResponse("/views/image/?error=Image+no+encontrada", status_code=302)
    try:
        image.path_256x256 = path_256x256
        image.path_512x512 = path_512x512
        session.add(image)
        session.commit()
        return RedirectResponse(f"/views/image/{id}?success=Image+actualizada", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(request, "image/edit.html",
            _ctx(request, image=image, error=str(e)),
        )


@router.post("/{id}/delete")
def delete(id: int, session: Session = Depends(get_session)):
    image = session.get(Image, id)
    if not image:
        return RedirectResponse("/views/image/?error=Image+no+encontrada", status_code=302)
    try:
        session.delete(image)
        session.commit()
        return RedirectResponse("/views/image/?success=Image+eliminada", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/views/image/?error={e}", status_code=302)
