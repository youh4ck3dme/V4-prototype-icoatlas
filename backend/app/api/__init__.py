from fastapi import APIRouter
from .endpoints.search import router as cz_router
from .endpoints.search_sk import router as sk_router
from .endpoints.search_pl import router as pl_router
from .endpoints.search_hu import router as hu_router

router = APIRouter()
router.include_router(cz_router, prefix="", tags=["search-cz"])
router.include_router(sk_router, prefix="/sk", tags=["search-sk"])
router.include_router(pl_router, prefix="/pl", tags=["search-pl"])
router.include_router(hu_router, prefix="/hu", tags=["search-hu"])
