from rest_framework import serializers

from apps.design_requests.models import DesignRequest


class DesignRequestSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)

    class Meta:
        model = DesignRequest
        fields = [
            'id',
            'client_email',
            'title',
            'description',
            'apparel_type',
            'quantity',
            'material',
            'design_image',
            'status',
            'created_at',
            'updated_at',
        ]
        # status is driven by the bidding flow, not set directly by clients.
        read_only_fields = [
            'id',
            'client_email',
            'status',
            'created_at',
            'updated_at',
        ]
