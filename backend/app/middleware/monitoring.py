"""
Monitoring middleware for request tracking and metrics.
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import sentry_sdk
from ..core.monitoring import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_CONNECTIONS


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track all HTTP requests with Prometheus metrics.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        # Start timer
        start_time = time.time()
        
        # Get endpoint path
        endpoint = request.url.path
        method = request.method
        
        try:
            # Process request
            response = await call_next(request)
            status = response.status_code
            
            # Record metrics
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
            
            # Record latency
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
        
        except Exception as e:
            # Record error
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
            
            # Record latency even on error
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            raise e
        
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()


class SentryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request context to Sentry events.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Add request context to Sentry
        with sentry_sdk.push_scope() as scope:
            # Add request information
            scope.set_context("request", {
                "url": str(request.url),
                "method": request.method,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
            })
            
            # Add user information if available
            # This can be customized based on your authentication system
            if hasattr(request.state, "user"):
                scope.set_user({
                    "id": getattr(request.state.user, "id", None),
                    "email": getattr(request.state.user, "email", None),
                })
            
            try:
                response = await call_next(request)
                return response
            
            except Exception as e:
                # Capture exception with context
                sentry_sdk.capture_exception(e)
                raise e
