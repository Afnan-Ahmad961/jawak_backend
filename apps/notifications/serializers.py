from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'message',
            'content_type',
            'object_id',
            'is_read',
            'created_at',
        ]
        read_only_fields = fields
