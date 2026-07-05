from django.urls import path

from apps.design_requests.views import (
    DesignRequestDetailView,
    DesignRequestListCreateView,
    ReferenceImageView,
)

app_name = 'design_requests'

urlpatterns = [
    path('', DesignRequestListCreateView.as_view(), name='list-create'),
    path('<int:request_id>/', DesignRequestDetailView.as_view(), name='detail'),
    path(
        '<int:request_id>/reference-images/',
        ReferenceImageView.as_view(),
        name='reference-images',
    ),
    path(
        '<int:request_id>/reference-images/<int:image_id>/',
        ReferenceImageView.as_view(),
        name='reference-image-detail',
    ),
]
