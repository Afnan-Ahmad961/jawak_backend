from django.contrib import admin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'reviewer', 'reviewee', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('reviewer__email', 'reviewee__email')
