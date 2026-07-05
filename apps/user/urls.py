from django.urls import path

from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.views import LogoutView
from rest_framework_simplejwt.views import TokenVerifyView

from .views import GoogleLogin, MeView

app_name = 'user'

urlpatterns = [
    # Google OAuth -> internal JWT
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    # JWT lifecycle
    path('auth/token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    # Current user
    path('me/', MeView.as_view(), name='me'),
]
