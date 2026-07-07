from django.urls import path

from apps.disputes.views import DisputeListCreateView, DisputeResolveView

app_name = 'disputes'

urlpatterns = [
    path('', DisputeListCreateView.as_view(), name='list-create'),
    path('<int:dispute_id>/', DisputeResolveView.as_view(), name='resolve'),
]
