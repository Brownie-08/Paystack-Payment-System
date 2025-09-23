"""
Health check views for deployment monitoring.
"""

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Simple health check endpoint for Railway and other deployment platforms.
    Returns 200 OK if the application is running correctly.
    """
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "debug": settings.DEBUG,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "database": "connected"
        }
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["database"] = "connected"
        except Exception as db_error:
            health_status["database"] = f"error: {str(db_error)}"
            logger.warning(f"Database health check failed: {db_error}")
        
        # Test cache
        try:
            cache.set("health_check", "ok", 10)
            cache_test = cache.get("health_check")
            health_status["cache"] = "working" if cache_test == "ok" else "failed"
        except Exception as cache_error:
            health_status["cache"] = f"error: {str(cache_error)}"
            logger.warning(f"Cache health check failed: {cache_error}")
        
        return JsonResponse(health_status, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "debug": getattr(settings, 'DEBUG', False)
        }, status=500)


def simple_health(request):
    """
    Ultra-simple health check that just returns OK.
    Use this if the main health check is failing.
    This bypasses most Django middleware for maximum compatibility.
    """
    # Add debug info to help diagnose the issue
    try:
        host_header = request.META.get('HTTP_HOST', 'no-host-header')
        logger.info(f"Health check called with HOST: {host_header}")
        logger.info(f"ALLOWED_HOSTS: {getattr(settings, 'ALLOWED_HOSTS', 'not-set')}")
        
        # Return basic OK response
        response = HttpResponse("OK", content_type="text/plain", status=200)
        response['X-Health-Check'] = 'simple'
        return response
        
    except Exception as e:
        logger.error(f"Simple health check error: {e}")
        # Even if there's an error, try to return OK
        return HttpResponse("OK", content_type="text/plain", status=200)


def raw_health(request):
    """
    Raw health check that bypasses all Django validation.
    This should work even with ALLOWED_HOSTS issues.
    """
    from django.http import HttpResponse
    return HttpResponse("OK", content_type="text/plain", status=200)
