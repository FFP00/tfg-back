from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from pwdlib import PasswordHash
from sqlmodel import Session, col, select

from app.config.auth import get_current_developer, oauth2_developer
from app.config.database import get_session
from app.database.models.DeveloperModel import Developer
from app.database.models.ImageModel import Image
from app.endpoint.schemas.developerSchema import (
    DeveloperImageUpload,
    DeveloperPatch,
    DeveloperPublic,
    DeveloperShow,
    LoginDeveloperResponse,
)

hasher = PasswordHash.recommended()
router = APIRouter()

_IMAGE_FIELDS = ("profile", "banner")


# ── Static routes first (before /{name}) ─────────────────────────────────────


@router.get("/me", response_model=LoginDeveloperResponse)
def me(
    token: str = Depends(oauth2_developer),
    current: Developer = Depends(get_current_developer),
) -> LoginDeveloperResponse:
    return LoginDeveloperResponse(
        access_token=token,
        developer=DeveloperShow.model_validate(current, from_attributes=True),
    )


@router.get("/", response_model=list[DeveloperPublic])
def index(search: str = "", session: Session = Depends(get_session)) -> list[Developer]:
    q = select(Developer).where(Developer.status)
    if search:
        q = q.where(col(Developer.name).ilike(f"%{search}%"))
    return list(session.exec(q).all())


@router.patch("/me", response_model=DeveloperShow)
def update_me(
    payload: DeveloperPatch,
    current: Developer = Depends(get_current_developer),
    session: Session = Depends(get_session),
) -> Developer:
    data = payload.model_dump(exclude_unset=True)

    if (
        "name" in data
        and session.exec(
            select(Developer).where(
                Developer.name == data["name"], Developer.id != current.id
            )
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Nombre ya en uso")

    if (
        "email" in data
        and session.exec(
            select(Developer).where(
                Developer.email == data["email"], Developer.id != current.id
            )
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Email ya en uso")

    if (
        "support_email" in data
        and session.exec(
            select(Developer).where(
                Developer.support_email == data["support_email"],
                Developer.id != current.id,
            )
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Support email ya en uso")

    if (
        "website_url" in data
        and data["website_url"]
        and session.exec(
            select(Developer).where(
                Developer.website_url == data["website_url"],
                Developer.id != current.id,
            )
        ).first()
    ):
        raise HTTPException(status_code=409, detail="Website URL ya en uso")

    if "password" in data:
        current.password = hasher.hash(data.pop("password"))

    current.sqlmodel_update(data)
    session.add(current)
    session.commit()
    session.refresh(current)
    return current


@router.patch("/me/image", status_code=204)
async def upload_image(
    body:    Annotated[DeveloperImageUpload, Form()],
    current: Developer = Depends(get_current_developer),
    session: Session   = Depends(get_session),
) -> Response:
    if not body.profile and not body.banner:
        raise HTTPException(
            status_code=400, detail="Se requiere al menos un campo: profile o banner"
        )

    image = session.get(Image, current.image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    if body.profile:
        image.profile = await body.profile.read()
    if body.banner:
        image.banner = await body.banner.read()

    session.add(image)
    session.commit()
    return Response(status_code=204)


# ── Dynamic routes ────────────────────────────────────────────────────────────


@router.get("/{name}/image/{field}")
def get_image(
    name: str, field: str, session: Session = Depends(get_session)
) -> Response:
    if field not in _IMAGE_FIELDS:
        raise HTTPException(
            status_code=400, detail=f"Campo inválido. Válidos: {list(_IMAGE_FIELDS)}"
        )
    developer = session.exec(
        select(Developer).where(Developer.name == name, Developer.status)
    ).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer no encontrado")
    image = session.get(Image, developer.image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    data: bytes | None = getattr(image, field, None)
    if not data:
        raise HTTPException(status_code=404, detail=f"Campo '{field}' vacío")
    return Response(content=data, media_type="image/jpeg")


@router.get("/{name}", response_model=DeveloperPublic)
def show(name: str, session: Session = Depends(get_session)) -> Developer:
    developer = session.exec(
        select(Developer).where(Developer.name == name, Developer.status)
    ).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer no encontrado")
    return developer
