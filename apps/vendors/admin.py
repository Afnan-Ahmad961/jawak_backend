from django.contrib import admin

from apps.vendors.models import VendorProfile


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'location', 'capacity', 'created_at')
    search_fields = ('company_name', 'user__email')
