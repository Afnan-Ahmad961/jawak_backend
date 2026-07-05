from rest_framework import serializers

from apps.design_requests.models import DesignReferenceImage, DesignRequest


class DesignReferenceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignReferenceImage
        fields = ['id', 'design_request', 'image', 'label', 'created_at']
        read_only_fields = ['id', 'design_request', 'created_at']


class DesignRequestSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    reference_images = DesignReferenceImageSerializer(many=True, read_only=True)

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
            'sizes',
            'color_preferences',
            'deadline',
            'design_image',
            'reference_images',
            'status',
            'created_at',
            'updated_at',
        ]
        # status is driven by the bidding flow, not set directly by clients.
        read_only_fields = [
            'id',
            'client_email',
            'reference_images',
            'status',
            'created_at',
            'updated_at',
        ]
