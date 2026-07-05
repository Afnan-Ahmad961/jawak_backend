from rest_framework import serializers

from apps.bids.models import Bid


class BidSerializer(serializers.ModelSerializer):
    vendor_company = serializers.CharField(
        source='vendor.company_name', read_only=True
    )

    class Meta:
        model = Bid
        fields = [
            'id',
            'design_request',
            'vendor',
            'vendor_company',
            'proposed_price',
            'delivery_days',
            'message',
            'status',
            'created_at',
            'updated_at',
        ]
        # vendor is taken from the caller; status changes via the status action.
        read_only_fields = [
            'id',
            'vendor',
            'vendor_company',
            'status',
            'created_at',
            'updated_at',
        ]


class BidStatusSerializer(serializers.Serializer):
    """Input for the accept/reject action."""

    status = serializers.ChoiceField(
        choices=[Bid.Status.ACCEPTED, Bid.Status.REJECTED]
    )
