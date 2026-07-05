from rest_framework import serializers

from apps.vendors.models import VendorProfile


class VendorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'user_email',
            'company_name',
            'location',
            'specialties',
            'capacity',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_email', 'created_at', 'updated_at']
