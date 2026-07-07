from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders import selectors, services
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer, ProductionUpdateSerializer


class OrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = selectors.orders_for_user(user=request.user)
        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return Response(OrderSerializer(qs, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get_order(self, request, order_id):
        try:
            order = selectors.order_get(order_id=order_id)
        except Order.DoesNotExist:
            raise Http404
        if not selectors.order_is_participant(order=order, user=request.user) \
                and not request.user.is_staff:
            raise PermissionDenied('You cannot view this order.')
        return order

    def get(self, request, order_id):
        order = self._get_order(request, order_id)
        return Response(OrderSerializer(order).data)


class ProductionUpdateCreateView(APIView):
    """Post a production milestone update — only the assigned vendor."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, order_id):
        try:
            order = selectors.order_get(order_id=order_id)
        except Order.DoesNotExist:
            raise Http404
        if order.vendor.user_id != request.user.id:
            raise PermissionDenied('Only the assigned vendor can post updates.')

        serializer = ProductionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            update = services.production_update_add(
                order=order, user=request.user, **serializer.validated_data
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(
            ProductionUpdateSerializer(update).data, status=status.HTTP_201_CREATED
        )


class OrderConfirmDeliveryView(APIView):
    """Client confirms delivery, completing the order."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = selectors.order_get(order_id=order_id)
        except Order.DoesNotExist:
            raise Http404
        if order.client_id != request.user.id:
            raise PermissionDenied('Only the client can confirm delivery.')

        try:
            order = services.order_confirm_delivery(order=order)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(OrderSerializer(order).data)
