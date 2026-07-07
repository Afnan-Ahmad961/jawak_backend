from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from rest_framework import generics, permissions

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


class MeView(generics.RetrieveAPIView):
    """Return the currently authenticated user's profile."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
