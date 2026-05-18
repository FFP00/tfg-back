from fastapi import FastAPI

from app.config.settings import settings
from app.endpoint.routes.roleRoute import router as role_router
from app.endpoint.routes.userRoute import router as user_router

app = FastAPI(title=settings.PROJECT_NAME)

# ── Routers ──────────────────────────────────────────────────────────────────
# Registrar aquí cada router conforme se vayan creando. Ejemplo:
#
#   from app.endpoint.route import users
#   app.include_router(users.router, prefix="/api/v1")

app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(role_router, prefix="/api/role", tags=["User"])
