from django.urls import path

from apps.vendors.views import VendorDetailView, VendorListView, VendorMeView

app_name = 'vendors'

urlpatterns = [
    path('', VendorListView.as_view(), name='list'),
    path('me/', VendorMeView.as_view(), name='me'),
    path('<int:vendor_id>/', VendorDetailView.as_view(), name='detail'),
]
