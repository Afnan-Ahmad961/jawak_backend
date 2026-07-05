"""
Root URL configuration for the Jawak backend.

Each feature app under `apps/` is mounted here under a versioned prefix, e.g.
    path('api/v1/user/', include('apps.user.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/user/', include('apps.user.urls')),
]
