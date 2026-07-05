from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only view of the authenticated user."""

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
            'created_at',
        ]
        read_only_fields = fields
