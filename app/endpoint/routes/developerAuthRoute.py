from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response
from pwdlib import PasswordHash
from sqlmodel import Session, select

from app.config.auth import (
    create_access_token,
    oauth2_developer,
    revoke_token,
)
from app.config.database import get_session
from app.database.models.DeveloperModel import Developer
from app.endpoint.schemas.authSchema import LoginForm
from app.endpoint.schemas.developerSchema import (
    DeveloperCreate,
    DeveloperShow,
    LoginDeveloperResponse,
)

hasher = PasswordHash.recommended()
router = APIRouter()


@router.post("/register", status_code=201)
def register(
    payload: DeveloperCreate, session: Session = Depends(get_session)
) -> Response:
    if session.exec(select(Developer).where(Developer.email == payload.email)).first():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    if session.exec(select(Developer).where(Developer.name == payload.name)).first():
        raise HTTPException(status_code=409, detail="Nombre ya registrado")
    if session.exec(
        select(Developer).where(Developer.support_email == payload.support_email)
    ).first():
        raise HTTPException(status_code=409, detail="Support email ya registrado")
    developer = Developer(
        name=payload.name,
        email=payload.email,
        support_email=payload.support_email,
        password=hasher.hash(payload.password),
        website_url=payload.website_url,
        status=False,
    )
    session.add(developer)
    session.commit()
    return Response(status_code=201)


@router.post("/login", response_model=LoginDeveloperResponse)
def login(
    form: Annotated[LoginForm, Form()], session: Session = Depends(get_session)
) -> LoginDeveloperResponse:
    developer = session.exec(
        select(Developer).where(Developer.email == form.username, Developer.status)
    ).first()
    if not developer or not hasher.verify(form.password, developer.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_access_token(
        {"sub": str(developer.id), "role": "developer"}, session
    )
    return LoginDeveloperResponse(
        access_token=token,
        developer=DeveloperShow.model_validate(developer, from_attributes=True),
    )


@router.post("/logout", status_code=204)
def logout(
    token: str = Depends(oauth2_developer), session: Session = Depends(get_session)
) -> Response:
    revoke_token(token, session)
    return Response(status_code=204)
