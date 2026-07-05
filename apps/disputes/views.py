from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status as http_status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.disputes import selectors, services
from apps.disputes.models import Dispute
from apps.disputes.serializers import DisputeResolveSerializer, DisputeSerializer


class DisputeListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = selectors.disputes_for_user(user=request.user)
        return Response(DisputeSerializer(qs, many=True).data)

    def post(self, request):
        serializer = DisputeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            dispute = services.dispute_open(
                order=data['order'],
                raised_by=request.user,
                reason=data['reason'],
                description=data.get('description', ''),
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(
            DisputeSerializer(dispute).data, status=http_status.HTTP_201_CREATED
        )


class DisputeResolveView(APIView):
    """Resolve or reject a dispute — admins only."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, dispute_id):
        user = request.user
        if not (user.is_staff or user.role == user.Role.ADMIN):
            raise PermissionDenied('Only admins can resolve disputes.')

        try:
            dispute = selectors.dispute_get(dispute_id=dispute_id)
        except Dispute.DoesNotExist:
            raise Http404

        serializer = DisputeResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            dispute = services.dispute_resolve(
                dispute=dispute,
                admin=request.user,
                status=serializer.validated_data['status'],
                resolution=serializer.validated_data.get('resolution', ''),
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(DisputeSerializer(dispute).data)
