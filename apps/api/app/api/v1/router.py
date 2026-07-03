from fastapi import APIRouter

from app.api.v1.routes import auth, exports, molecules, reports

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(molecules.router)
api_router.include_router(reports.router)
api_router.include_router(exports.router)
