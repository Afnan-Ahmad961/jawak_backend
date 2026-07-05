from django.contrib import admin

from apps.design_requests.models import DesignRequest


@admin.register(DesignRequest)
class DesignRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'apparel_type', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'apparel_type')
    search_fields = ('title', 'client__email')
