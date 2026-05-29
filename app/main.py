from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings

# ── Auth ──────────────────────────────────────────────────────────────────────
from app.endpoint.routes.authRoute import router as auth_router

# ── API routes ────────────────────────────────────────────────────────────────
from app.endpoint.routes.countryRoute import router as country_router
from app.endpoint.routes.currencyRoute import router as currency_router
from app.endpoint.routes.customerRoute import router as customer_router
from app.endpoint.routes.customerTitleRoute import router as customer_title_router
from app.endpoint.routes.developerRoute import router as developer_router
from app.endpoint.routes.friendshipRoute import router as friendship_router
from app.endpoint.routes.genreRoute import router as genre_router
from app.endpoint.routes.genreTitleRoute import router as genre_title_router
from app.endpoint.routes.imageRoute import router as image_router
from app.endpoint.routes.mediaRoute import router as media_router
from app.endpoint.routes.reviewRoute import router as review_router
from app.endpoint.routes.titleRoute import router as title_router
from app.endpoint.routes.titleTransactionRoute import router as title_transaction_router
from app.endpoint.routes.transactionRoute import router as transaction_router
from app.endpoint.routes.walletRoute import router as wallet_router

# ── View routes (HTML) ────────────────────────────────────────────────────────
from app.endpoint.views.countryView import router as country_view_router
from app.endpoint.views.currencyView import router as currency_view_router
from app.endpoint.views.customerTitleView import router as customer_title_view_router
from app.endpoint.views.customerView import router as customer_view_router
from app.endpoint.views.dashboardView import router as dashboard_view_router
from app.endpoint.views.developerView import router as developer_view_router
from app.endpoint.views.friendshipView import router as friendship_view_router
from app.endpoint.views.genreTitleView import router as genre_title_view_router
from app.endpoint.views.genreView import router as genre_view_router
from app.endpoint.views.imageView import router as image_view_router
from app.endpoint.views.mediaView import router as media_view_router
from app.endpoint.views.reviewView import router as review_view_router
from app.endpoint.views.titleTransactionView import (
    router as title_transaction_view_router,
)
from app.endpoint.views.titleView import router as title_view_router
from app.endpoint.views.transactionView import router as transaction_view_router
from app.endpoint.views.walletView import router as wallet_view_router

app = FastAPI(title=settings.PROJECT_NAME)

app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# ── Auth Routers ──────────────────────────────────────────────────────────────

app.include_router(auth_router,              prefix="/auth",              tags=["Auth"])

# ── API Routers ───────────────────────────────────────────────────────────────

app.include_router(currency_router,          prefix="/api/currency",          tags=["Currency"])
app.include_router(country_router,           prefix="/api/country",           tags=["Country"])
app.include_router(image_router,             prefix="/api/image",             tags=["Image"])
app.include_router(media_router,             prefix="/api/media",             tags=["Media"])
app.include_router(genre_router,             prefix="/api/genre",             tags=["Genre"])
app.include_router(developer_router,         prefix="/api/developer",         tags=["Developer"])
app.include_router(customer_router,          prefix="/api/customer",          tags=["Customer"])
app.include_router(title_router,             prefix="/api/title",             tags=["Title"])
app.include_router(review_router,            prefix="/api/review",            tags=["Review"])
app.include_router(wallet_router,            prefix="/api/wallet",            tags=["Wallet"])
app.include_router(transaction_router,       prefix="/api/transaction",       tags=["Transaction"])
app.include_router(friendship_router,        prefix="/api/friendship",        tags=["Friendship"])
app.include_router(customer_title_router,    prefix="/api/customer_title",    tags=["CustomerTitle"])
app.include_router(genre_title_router,       prefix="/api/genre_title",       tags=["GenreTitle"])
app.include_router(title_transaction_router, prefix="/api/title_transaction", tags=["TitleTransaction"])

# ── View Routers (HTML) ───────────────────────────────────────────────────────

app.include_router(dashboard_view_router,         prefix="/views",                        tags=["Views"])
app.include_router(currency_view_router,          prefix="/views/currency",               tags=["Views"])
app.include_router(image_view_router,             prefix="/views/image",                  tags=["Views"])
app.include_router(media_view_router,             prefix="/views/media",                  tags=["Views"])
app.include_router(genre_view_router,             prefix="/views/genre",                  tags=["Views"])
app.include_router(country_view_router,           prefix="/views/country",                tags=["Views"])
app.include_router(developer_view_router,         prefix="/views/developer",              tags=["Views"])
app.include_router(customer_view_router,          prefix="/views/customer",               tags=["Views"])
app.include_router(title_view_router,             prefix="/views/title",                  tags=["Views"])
app.include_router(wallet_view_router,            prefix="/views/wallet",                 tags=["Views"])
app.include_router(friendship_view_router,        prefix="/views/friendship",             tags=["Views"])
app.include_router(genre_title_view_router,       prefix="/views/genre_title",            tags=["Views"])
app.include_router(customer_title_view_router,    prefix="/views/customer_title",         tags=["Views"])
app.include_router(transaction_view_router,       prefix="/views/transaction",            tags=["Views"])
app.include_router(review_view_router,            prefix="/views/review",                 tags=["Views"])
app.include_router(title_transaction_view_router, prefix="/views/title_transaction",      tags=["Views"])
