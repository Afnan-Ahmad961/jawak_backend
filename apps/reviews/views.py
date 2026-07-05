from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reviews import selectors, services
from apps.reviews.serializers import ReviewSerializer
from apps.vendors.models import VendorProfile


class ReviewListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List reviews, filtered by `?vendor=<id>` or `?order=<id>`."""
        vendor = None
        vendor_id = request.query_params.get('vendor')
        if vendor_id:
            try:
                vendor = VendorProfile.objects.get(id=vendor_id)
            except VendorProfile.DoesNotExist:
                raise Http404

        order_id = request.query_params.get('order')
        qs = selectors.reviews_list(vendor=vendor, order=order_id or None)
        return Response(ReviewSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            review = services.review_create(
                order=data['order'],
                reviewer=request.user,
                rating=data['rating'],
                comment=data.get('comment', ''),
            )
        except DjangoValidationError as exc:
            raise ValidationError(
                exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
            )
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
