from django.urls import path

from apps.orders.views import (
    OrderConfirmDeliveryView,
    OrderDetailView,
    OrderListView,
    ProductionUpdateCreateView,
)

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='list'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='detail'),
    path(
        '<int:order_id>/production-updates/',
        ProductionUpdateCreateView.as_view(),
        name='production-update',
    ),
    path(
        '<int:order_id>/confirm-delivery/',
        OrderConfirmDeliveryView.as_view(),
        name='confirm-delivery',
    ),
]
