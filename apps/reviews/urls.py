from django.urls import path

from apps.reviews.views import ReviewListCreateView

app_name = 'reviews'

urlpatterns = [
    path('', ReviewListCreateView.as_view(), name='list-create'),
]
