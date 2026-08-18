from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client, OAuth2Error
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from .serializers import UserSerializer


class GoogleLogin(SocialLoginView):
    """Exchange a Google OAuth2 access token (or auth code) for internal JWTs.

    The client obtains a Google token via the frontend, POSTs it here as
    ``{"access_token": "..."}`` (or ``{"code": "..."}``), and receives the
    platform's own access/refresh JWTs in return. On first login a matching
    User is created via allauth.
    """

    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL

    def post(self, request, *args, **kwargs):
        # A malformed/expired/revoked Google token makes allauth raise
        # OAuth2Error while it tries to exchange or verify it with Google.
        # That's bad client input, so surface it as a 400 instead of letting
        # it bubble up as an unhandled 500.
        try:
            return super().post(request, *args, **kwargs)
        except OAuth2Error as exc:
            raise ValidationError(
                {'access_token': 'Invalid or expired Google token.'}
            ) from exc


class MeView(generics.RetrieveAPIView):
    """Return the currently authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
