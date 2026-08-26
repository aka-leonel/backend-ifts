from fastapi import APIRouter
from app.features.recursos.routers import recursos, convenios, talentotech

recursos_main_router = APIRouter()

recursos_main_router.include_router(recursos.router)
recursos_main_router.include_router(convenios.router)
recursos_main_router.include_router(talentotech.router)
