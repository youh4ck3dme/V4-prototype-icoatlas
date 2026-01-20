"""
Monitoring module for Sentry and Prometheus integration.
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

SEARCH_COUNT = Counter(
    'search_requests_total',
    'Total search requests by country',
    ['country', 'status']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits'
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses'
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

DB_QUERY_COUNT = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation']
)

DB_QUERY_LATENCY = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['operation']
)


def init_sentry(dsn: Optional[str] = None, traces_sample_rate: float = 0.1, environment: str = "development"):
    """
    Initialize Sentry SDK for error tracking.
    
    Args:
        dsn: Sentry DSN (Data Source Name)
        traces_sample_rate: Percentage of traces to send to Sentry (0.0 to 1.0)
        environment: Environment name (development, staging, production)
    """
    if not dsn:
        return
    
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=traces_sample_rate,
        environment=environment,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Filter sensitive data
        before_send=filter_sensitive_data,
    )


def filter_sensitive_data(event, hint):
    """
    Filter sensitive data from Sentry events.
    
    Removes passwords, tokens, and other sensitive information.
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '[Filtered]'
    
    # Remove sensitive POST data
    if 'request' in event and 'data' in event['request']:
        data = event['request']['data']
        if isinstance(data, dict):
            sensitive_fields = ['password', 'token', 'secret', 'api_key']
            for field in sensitive_fields:
                if field in data:
                    data[field] = '[Filtered]'
    
    return event


def capture_exception(exception: Exception, context: Optional[dict] = None):
    """
    Capture an exception and send it to Sentry.
    
    Args:
        exception: The exception to capture
        context: Additional context to include
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", context: Optional[dict] = None):
    """
    Capture a message and send it to Sentry.
    
    Args:
        message: The message to capture
        level: Message level (debug, info, warning, error, fatal)
        context: Additional context to include
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        sentry_sdk.capture_message(message, level=level)


def get_metrics():
    """
    Get Prometheus metrics in the format expected by Prometheus.
    
    Returns:
        Tuple of (metrics_data, content_type)
    """
    return generate_latest(), CONTENT_TYPE_LATEST
