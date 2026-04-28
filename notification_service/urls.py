"""notification_service URL configuration."""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health(_request):
    return JsonResponse({'status': 'ok', 'service': 'notification-service'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('notifications.urls')),
    path('health/', health, name='health'),
    path('', include('django_prometheus.urls')),  # exposes /metrics
]
