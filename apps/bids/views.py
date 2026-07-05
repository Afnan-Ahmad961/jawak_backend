from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bids import selectors, services
from apps.bids.models import Bid
from apps.bids.serializers import BidSerializer, BidStatusSerializer
from apps.design_requests import selectors as request_selectors
from apps.design_requests.models import DesignRequest
from apps.vendors import selectors as vendor_selectors


class BidListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List bids.

        `?request=<id>` -> bids for that request (owner/staff see all, a
        vendor sees only their own). No param -> the caller's own bids.
        """
        request_id = request.query_params.get('request')
        user = request.user

        if not request_id:
            vendor = vendor_selectors.vendor_get_for_user(user=user)
            if vendor is None:
                return Response([])
            qs = selectors.bids_for_vendor(vendor=vendor)
            return Response(BidSerializer(qs, many=True).data)

        try:
            design_request = request_selectors.design_request_get(request_id=request_id)
        except DesignRequest.DoesNotExist:
            raise Http404

        qs = selectors.bids_for_request(design_request=design_request)
        if design_request.client_id != user.id and not user.is_staff:
            # A vendor may only see their own bid on someone else's request.
            vendor = vendor_selectors.vendor_get_for_user(user=user)
            qs = qs.filter(vendor=vendor) if vendor else Bid.objects.none()

        return Response(BidSerializer(qs, many=True).data)

    def post(self, request):
        """Place a bid on a request (vendors only)."""
        serializer = BidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vendor = vendor_selectors.vendor_get_for_user(user=request.user)
        if vendor is None:
            raise PermissionDenied('You need a vendor profile to place a bid.')

        try:
            bid = services.bid_place(vendor=vendor, **serializer.validated_data)
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            )
        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)


class BidDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, bid_id):
        try:
            bid = selectors.bid_get(bid_id=bid_id)
        except Bid.DoesNotExist:
            raise Http404

        user = request.user
        is_owner = bid.design_request.client_id == user.id
        is_bidder = bid.vendor.user_id == user.id
        if not (is_owner or is_bidder or user.is_staff):
            raise PermissionDenied('You cannot view this bid.')

        return Response(BidSerializer(bid).data)


class BidStatusUpdateView(APIView):
    """Accept or reject a bid — only the client who owns the request."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, bid_id):
        try:
            bid = selectors.bid_get(bid_id=bid_id)
        except Bid.DoesNotExist:
            raise Http404

        if bid.design_request.client_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Only the request owner can update bid status.')

        serializer = BidStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        try:
            if new_status == Bid.Status.ACCEPTED:
                bid = services.bid_accept(bid=bid)
            else:
                bid = services.bid_reject(bid=bid)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)

        return Response(BidSerializer(bid).data)
