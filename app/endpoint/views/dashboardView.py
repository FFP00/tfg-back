from fastapi import APIRouter, Request

from app.config.templates import templates

router = APIRouter()


@router.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")
