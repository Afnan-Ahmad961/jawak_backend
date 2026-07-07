from rest_framework import serializers

from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)
    reviewee_email = serializers.EmailField(source='reviewee.email', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'order',
            'reviewer',
            'reviewer_email',
            'reviewee',
            'reviewee_email',
            'rating',
            'comment',
            'created_at',
        ]
        # reviewer/reviewee are derived from the order + caller in the service.
        read_only_fields = [
            'id',
            'reviewer',
            'reviewer_email',
            'reviewee',
            'reviewee_email',
            'created_at',
        ]
