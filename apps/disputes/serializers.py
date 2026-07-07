from rest_framework import serializers

from apps.disputes.models import Dispute


class DisputeSerializer(serializers.ModelSerializer):
    raised_by_email = serializers.EmailField(
        source='raised_by.email', read_only=True
    )

    class Meta:
        model = Dispute
        fields = [
            'id',
            'order',
            'raised_by',
            'raised_by_email',
            'reason',
            'description',
            'status',
            'resolution',
            'resolved_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'raised_by',
            'raised_by_email',
            'status',
            'resolution',
            'resolved_by',
            'created_at',
            'updated_at',
        ]


class DisputeResolveSerializer(serializers.Serializer):
    """Admin input for resolving a dispute."""

    status = serializers.ChoiceField(
        choices=[Dispute.Status.RESOLVED, Dispute.Status.REJECTED]
    )
    resolution = serializers.CharField(allow_blank=True, required=False)
