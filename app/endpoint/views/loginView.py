from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response
from pwdlib import PasswordHash
from sqlmodel import Session, or_, select

from app.config.auth import create_access_token, revoke_token
from app.config.database import get_session
from app.config.templates import templates
from app.database.models.UserModel import User

hasher = PasswordHash.recommended()
router = APIRouter()


@router.get("/")
def login_page(request: Request) -> Response:
    return templates.TemplateResponse(request, "login.html", {"request": request})


@router.post("/")
def login(
    request:  Request,
    username: str     = Form(...),
    password: str     = Form(...),
    session:  Session = Depends(get_session),
) -> Response:
    user = session.exec(
        select(User).where(
            or_(User.email == username, User.name == username),
            User.type == "ADM",
        )
    ).first()
    if not user or not hasher.verify(password, user.password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "Credenciales incorrectas"},
        )
    token = create_access_token({"sub": str(user.id), "role": "admin"}, user.id, session)
    response = RedirectResponse("/views/", status_code=302)
    response.set_cookie("admin_token", token, httponly=True, samesite="lax")
    return response


@router.post("/logout")
def logout(request: Request, session: Session = Depends(get_session)) -> Response:
    token = request.cookies.get("admin_token")
    if token:
        revoke_token(token, session)
    response = RedirectResponse("/views/login", status_code=302)
    response.delete_cookie("admin_token")
    return response
