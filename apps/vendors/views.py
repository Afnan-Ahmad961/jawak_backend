from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.vendors import selectors, services
from apps.vendors.models import VendorProfile
from apps.vendors.serializers import VendorProfileSerializer


class VendorListView(ListAPIView):
    """Browse all vendor profiles (used by clients comparing manufacturers)."""

    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return selectors.vendor_list()


class VendorDetailView(RetrieveAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'vendor_id'

    def get_queryset(self):
        return selectors.vendor_list()


class VendorMeView(APIView):
    """Create, read, and update the authenticated user's own vendor profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = selectors.vendor_get_for_user(user=request.user)
        if profile is None:
            raise Http404
        return Response(VendorProfileSerializer(profile).data)

    def post(self, request):
        serializer = VendorProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            profile = services.vendor_profile_create(
                user=request.user, **serializer.validated_data
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(
            VendorProfileSerializer(profile).data, status=status.HTTP_201_CREATED
        )

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, *, partial):
        profile = selectors.vendor_get_for_user(user=request.user)
        if profile is None:
            raise Http404
        serializer = VendorProfileSerializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            profile = services.vendor_profile_update(
                profile=profile, data=serializer.validated_data
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        return Response(VendorProfileSerializer(profile).data)
