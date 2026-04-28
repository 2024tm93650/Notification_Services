"""notification_service URL configuration."""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health(_request):
    return JsonResponse({'status': 'ok', 'service': 'notification-service'})


def ready(_request):
    # Readiness probe: verifies DB connectivity
    from django.db import connection
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'ready', 'service': 'notification-service'})
    except Exception as exc:  # pragma: no cover
        return JsonResponse({'status': 'not_ready', 'error': str(exc)}, status=503)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('notifications.urls')),
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('', include('django_prometheus.urls')),  # exposes /metrics
]
