from fastapi import APIRouter

from src.routers import auth, health, items

# Versioned API routes; mounted under settings.api_v1_prefix in main.py
api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(items.router)

# Authentication is enforced for every request by middlewares/auth.py.
# These (method, path) pairs, relative to the API prefix, are the only explicit exceptions.
PUBLIC_API_ROUTES = frozenset({
    ("POST", "/auth/login"),
})

__all__ = ["PUBLIC_API_ROUTES", "api_router", "health"]
