"""
Metrics endpoint for Prometheus.
"""
from fastapi import APIRouter, Response
from ...core.monitoring import get_metrics

router = APIRouter()


@router.get("/metrics", tags=["monitoring"])
async def metrics():
    """
    Expose Prometheus metrics.
    
    Returns metrics in Prometheus format for scraping.
    """
    metrics_data, content_type = get_metrics()
    return Response(content=metrics_data, media_type=content_type)
