from django.urls import path

from apps.vendors.views import (
    PortfolioView,
    VendorDetailView,
    VendorListView,
    VendorMeView,
)

app_name = 'vendors'

urlpatterns = [
    path('', VendorListView.as_view(), name='list'),
    path('me/', VendorMeView.as_view(), name='me'),
    path('me/portfolio/', PortfolioView.as_view(), name='portfolio'),
    path(
        'me/portfolio/<int:item_id>/',
        PortfolioView.as_view(),
        name='portfolio-detail',
    ),
    path('<int:vendor_id>/', VendorDetailView.as_view(), name='detail'),
]
