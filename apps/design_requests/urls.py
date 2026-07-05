from django.urls import path

from apps.design_requests.views import (
    DesignRequestDetailView,
    DesignRequestListCreateView,
)

app_name = 'design_requests'

urlpatterns = [
    path('', DesignRequestListCreateView.as_view(), name='list-create'),
    path('<int:request_id>/', DesignRequestDetailView.as_view(), name='detail'),
]
