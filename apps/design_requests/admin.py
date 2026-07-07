from django.contrib import admin

from apps.design_requests.models import DesignReferenceImage, DesignRequest


class DesignReferenceImageInline(admin.TabularInline):
    model = DesignReferenceImage
    extra = 0


@admin.register(DesignRequest)
class DesignRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'apparel_type', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'apparel_type')
    search_fields = ('title', 'client__email')
    inlines = [DesignReferenceImageInline]
