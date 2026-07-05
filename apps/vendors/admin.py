from django.contrib import admin

from apps.vendors.models import PortfolioItem, VendorProfile


class PortfolioItemInline(admin.TabularInline):
    model = PortfolioItem
    extra = 0


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'user',
        'location',
        'capacity',
        'avg_rating',
        'review_count',
        'created_at',
    )
    search_fields = ('company_name', 'user__email')
    inlines = [PortfolioItemInline]
