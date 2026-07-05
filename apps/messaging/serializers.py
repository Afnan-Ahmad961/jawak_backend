from rest_framework import serializers

from apps.messaging.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source='sender.email', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'sender_email',
            'body',
            'is_read',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'conversation',
            'sender',
            'sender_email',
            'is_read',
            'created_at',
        ]


class ConversationSerializer(serializers.ModelSerializer):
    request_title = serializers.CharField(
        source='design_request.title', read_only=True
    )
    vendor_company = serializers.CharField(
        source='vendor.company_name', read_only=True
    )

    class Meta:
        model = Conversation
        fields = [
            'id',
            'design_request',
            'request_title',
            'vendor',
            'vendor_company',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'request_title',
            'vendor_company',
            'created_at',
            'updated_at',
        ]


class ConversationStartSerializer(serializers.Serializer):
    """Input for starting/opening a conversation."""

    design_request = serializers.IntegerField()
    vendor = serializers.IntegerField()
