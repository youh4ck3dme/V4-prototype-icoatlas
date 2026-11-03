from fastapi import APIRouter
from .endpoints.search import router as cz_router
from .endpoints.search_sk import router as sk_router
from .endpoints.search_pl import router as pl_router
from .endpoints.search_hu import router as hu_router
from .endpoints.search_v4 import router as v4_router
from .endpoints.users import router as users_router
from .endpoints.payment import router as payment_router

router = APIRouter()
router.include_router(cz_router, prefix="", tags=["search-cz"])
router.include_router(sk_router, prefix="/sk", tags=["search-sk"])
router.include_router(pl_router, prefix="/pl", tags=["search-pl"])
router.include_router(hu_router, prefix="/hu", tags=["search-hu"])
router.include_router(v4_router, prefix="/v4", tags=["search-v4"])
router.include_router(users_router, prefix="")
router.include_router(payment_router, prefix="", tags=["payment"])
