from fastapi import FastAPI

from app.endpoint.route.role import router as role_router
from app.endpoint.route.user import router as user_router
from app.settings import settings

app = FastAPI(title=settings.PROJECT_NAME)

# ── Routers ──────────────────────────────────────────────────────────────────
# Registrar aquí cada router conforme se vayan creando. Ejemplo:
#
#   from app.endpoint.route import users
#   app.include_router(users.router, prefix="/api/v1")

app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(role_router, prefix="/api/role", tags=["User"])
