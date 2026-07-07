from django.http import Http404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import selectors, services
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread_only = request.query_params.get('unread') == 'true'
        qs = selectors.notifications_for_user(
            user=request.user, unread_only=unread_only
        )
        return Response(NotificationSerializer(qs, many=True).data)


class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id):
        try:
            notification = selectors.notification_get(
                notification_id=notification_id, user=request.user
            )
        except Notification.DoesNotExist:
            raise Http404
        notification = services.notification_mark_read(notification=notification)
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = services.notifications_mark_all_read(user=request.user)
        return Response({'marked_read': updated})
