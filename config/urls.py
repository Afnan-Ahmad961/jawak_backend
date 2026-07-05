"""
Root URL configuration for the Jawak backend.

Each feature app under `apps/` is mounted here under a versioned prefix, e.g.
    path('api/v1/user/', include('apps.user.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/user/', include('apps.user.urls')),
    path('api/v1/vendors/', include('apps.vendors.urls')),
    path('api/v1/requests/', include('apps.design_requests.urls')),
    path('api/v1/bids/', include('apps.bids.urls')),
]

# Serve uploaded media from local storage during development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
