from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics import selectors


class AnalyticsOverviewView(APIView):
    """Aggregate marketplace metrics for the admin dashboard."""

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(selectors.overview())
