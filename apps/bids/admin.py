from django.contrib import admin

from apps.bids.models import Bid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'design_request',
        'vendor',
        'proposed_price',
        'delivery_days',
        'status',
        'created_at',
    )
    list_filter = ('status',)
    search_fields = ('design_request__title', 'vendor__company_name')
