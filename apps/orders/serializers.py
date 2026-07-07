from rest_framework import serializers

from apps.orders.models import Order, ProductionUpdate


class ProductionUpdateSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)

    class Meta:
        model = ProductionUpdate
        fields = [
            'id',
            'order',
            'stage',
            'stage_display',
            'note',
            'image',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['id', 'order', 'created_by', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    vendor_company = serializers.CharField(
        source='vendor.company_name', read_only=True
    )
    client_email = serializers.EmailField(source='client.email', read_only=True)
    request_title = serializers.CharField(
        source='design_request.title', read_only=True
    )
    production_updates = ProductionUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'bid',
            'design_request',
            'request_title',
            'vendor',
            'vendor_company',
            'client',
            'client_email',
            'final_price',
            'deadline',
            'current_stage',
            'status',
            'production_updates',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
