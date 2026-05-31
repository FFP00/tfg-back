from fastapi import FastAPI

from app.config.settings import settings

# ── API routes ────────────────────────────────────────────────────────────────
from app.endpoint.routes.countryRoute import router as country_router
from app.endpoint.routes.currencyRoute import router as currency_router

# ── Auth ──────────────────────────────────────────────────────────────────────
from app.endpoint.routes.customerAuthRoute import router as customer_auth_router
from app.endpoint.routes.customerRoute import router as customer_router
from app.endpoint.routes.developerAuthRoute import router as developer_auth_router
from app.endpoint.routes.developerRoute import router as developer_router
from app.endpoint.routes.friendshipRoute import router as friendship_router
from app.endpoint.routes.genreRoute import router as genre_router
from app.endpoint.routes.titleRoute import router as title_router
from app.endpoint.routes.transactionRoute import router as transaction_router

# ── View routes (HTML admin panel) ────────────────────────────────────────────
from app.endpoint.views.countryView import router as country_view_router
from app.endpoint.views.currencyView import router as currency_view_router
from app.endpoint.views.customerView import router as customer_view_router
from app.endpoint.views.dashboardView import router as dashboard_view_router
from app.endpoint.views.developerView import router as developer_view_router
from app.endpoint.views.friendshipView import router as friendship_view_router
from app.endpoint.views.genreView import router as genre_view_router
from app.endpoint.views.reviewView import router as review_view_router
from app.endpoint.views.titleView import router as title_view_router
from app.endpoint.views.tokenView import router as token_view_router
from app.endpoint.views.transactionView import router as transaction_view_router

app = FastAPI(title=settings.PROJECT_NAME)

# ── Auth ──────────────────────────────────────────────────────────────────────

app.include_router(customer_auth_router,  prefix="/auth/customer",  tags=["Auth"])
app.include_router(developer_auth_router, prefix="/auth/developer", tags=["Auth"])

# ── API ───────────────────────────────────────────────────────────────────────

app.include_router(currency_router,    prefix="/api/currency",    tags=["Currency"])
app.include_router(country_router,     prefix="/api/country",     tags=["Country"])
app.include_router(genre_router,       prefix="/api/genre",       tags=["Genre"])
app.include_router(developer_router,   prefix="/api/developer",   tags=["Developer"])
app.include_router(customer_router,    prefix="/api/customer",    tags=["Customer"])
app.include_router(title_router,       prefix="/api/title",       tags=["Title"])
app.include_router(transaction_router, prefix="/api/transaction", tags=["Transaction"])
app.include_router(friendship_router,  prefix="/api/friendship",  tags=["Friendship"])

# ── Admin panel (Jinja2 views) ────────────────────────────────────────────────

_VIEW = {"tags": ["Views"], "include_in_schema": False}

app.include_router(dashboard_view_router,   prefix="/views",              **_VIEW)
app.include_router(currency_view_router,    prefix="/views/currency",     **_VIEW)
app.include_router(genre_view_router,       prefix="/views/genre",        **_VIEW)
app.include_router(country_view_router,     prefix="/views/country",      **_VIEW)
app.include_router(developer_view_router,   prefix="/views/developer",    **_VIEW)
app.include_router(customer_view_router,    prefix="/views/customer",     **_VIEW)
app.include_router(title_view_router,       prefix="/views/title",        **_VIEW)
app.include_router(friendship_view_router,  prefix="/views/friendship",   **_VIEW)
app.include_router(transaction_view_router, prefix="/views/transaction",  **_VIEW)
app.include_router(review_view_router,      prefix="/views/review",       **_VIEW)
app.include_router(token_view_router,       prefix="/views/token",        **_VIEW)
