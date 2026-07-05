from rest_framework import serializers

from .models import User, VendorProfile


class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'company_name',
            'location',
            'specialties',
            'capacity',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """Read-only view of the authenticated user, including the vendor
    profile when present."""

    vendor_profile = VendorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'role',
            'google_uid',
            'first_name',
            'last_name',
            'vendor_profile',
            'created_at',
        ]
        read_only_fields = fields
