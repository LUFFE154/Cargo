from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.folders import router as folders_router
from app.api.routes.health import router as health_router
from app.api.routes.search import router as search_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.transfers import router as transfers_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(folders_router)
api_router.include_router(health_router)
api_router.include_router(search_router)
api_router.include_router(uploads_router)
api_router.include_router(transfers_router)
