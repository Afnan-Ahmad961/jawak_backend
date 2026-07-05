from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.design_requests import selectors, services
from apps.design_requests.models import DesignReferenceImage, DesignRequest
from apps.design_requests.serializers import (
    DesignReferenceImageSerializer,
    DesignRequestSerializer,
)


class DesignRequestListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # MultiPartParser/FormParser handle the design-image file upload.
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        user = request.user
        # Clients see their own requests; everyone else sees the open board.
        if user.role == user.Role.CLIENT:
            qs = selectors.design_request_list(client=user)
        else:
            qs = selectors.open_requests()

        status_param = request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        return Response(DesignRequestSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.role != request.user.Role.CLIENT and not request.user.is_staff:
            raise PermissionDenied('Only clients can post design requests.')
        serializer = DesignRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        design_request = services.design_request_create(
            client=request.user, **serializer.validated_data
        )
        return Response(
            DesignRequestSerializer(design_request).data,
            status=status.HTTP_201_CREATED,
        )


class DesignRequestDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, request_id):
        try:
            return selectors.design_request_get(request_id=request_id)
        except DesignRequest.DoesNotExist:
            raise Http404

    def _require_owner(self, request, design_request):
        if design_request.client_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('You can only modify your own requests.')

    def get(self, request, request_id):
        return Response(DesignRequestSerializer(self.get_object(request_id)).data)

    def put(self, request, request_id):
        return self._update(request, request_id, partial=False)

    def patch(self, request, request_id):
        return self._update(request, request_id, partial=True)

    def _update(self, request, request_id, *, partial):
        design_request = self.get_object(request_id)
        self._require_owner(request, design_request)
        serializer = DesignRequestSerializer(
            design_request, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        design_request = services.design_request_update(
            design_request=design_request, data=serializer.validated_data
        )
        return Response(DesignRequestSerializer(design_request).data)

    def delete(self, request, request_id):
        design_request = self.get_object(request_id)
        self._require_owner(request, design_request)
        services.design_request_delete(design_request=design_request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReferenceImageView(APIView):
    """Add or remove reference images (article artwork) on a request."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_request(self, request, request_id):
        try:
            design_request = selectors.design_request_get(request_id=request_id)
        except DesignRequest.DoesNotExist:
            raise Http404
        if design_request.client_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('You can only modify your own requests.')
        return design_request

    def post(self, request, request_id):
        design_request = self._get_request(request, request_id)
        serializer = DesignReferenceImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reference = services.reference_image_add(
                design_request=design_request, **serializer.validated_data
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(
            DesignReferenceImageSerializer(reference).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, request_id, image_id):
        design_request = self._get_request(request, request_id)
        try:
            reference = selectors.reference_image_get(
                design_request=design_request, image_id=image_id
            )
        except DesignReferenceImage.DoesNotExist:
            raise Http404
        services.reference_image_delete(reference=reference)
        return Response(status=status.HTTP_204_NO_CONTENT)
