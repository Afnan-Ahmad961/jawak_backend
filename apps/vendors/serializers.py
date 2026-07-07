from rest_framework import serializers

from apps.vendors.models import PortfolioItem, VendorProfile


class PortfolioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioItem
        fields = ['id', 'vendor', 'image', 'title', 'description', 'created_at']
        read_only_fields = ['id', 'vendor', 'created_at']


class VendorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    portfolio_items = PortfolioItemSerializer(many=True, read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'user_email',
            'company_name',
            'location',
            'specialties',
            'capacity',
            'avg_rating',
            'review_count',
            'portfolio_items',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user_email',
            'avg_rating',
            'review_count',
            'portfolio_items',
            'created_at',
            'updated_at',
        ]
