from django.urls import path

from apps.bids.views import (
    BidDetailView,
    BidListCreateView,
    BidStatusUpdateView,
    BidWithdrawView,
)

app_name = 'bids'

urlpatterns = [
    path('', BidListCreateView.as_view(), name='list-create'),
    path('<int:bid_id>/', BidDetailView.as_view(), name='detail'),
    path('<int:bid_id>/status/', BidStatusUpdateView.as_view(), name='status'),
    path('<int:bid_id>/withdraw/', BidWithdrawView.as_view(), name='withdraw'),
]
