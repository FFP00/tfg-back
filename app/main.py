from fastapi import FastAPI

from app.settings import settings

app = FastAPI(title=settings.PROJECT_NAME)

# ── Routers ──────────────────────────────────────────────────────────────────
# Registrar aquí cada router conforme se vayan creando. Ejemplo:
#
#   from app.endpoint.route import users
#   app.include_router(users.router, prefix="/api/v1")

app.include_router(usuario.router, prefix="/api/user", tags=["User"])