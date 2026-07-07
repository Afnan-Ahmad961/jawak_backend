from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    NotificationReadAllView,
    NotificationReadView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('read-all/', NotificationReadAllView.as_view(), name='read-all'),
    path('<int:notification_id>/read/', NotificationReadView.as_view(), name='read'),
]
