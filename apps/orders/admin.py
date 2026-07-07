from django.contrib import admin

from apps.orders.models import Order, ProductionUpdate


class ProductionUpdateInline(admin.TabularInline):
    model = ProductionUpdate
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'design_request',
        'vendor',
        'client',
        'final_price',
        'current_stage',
        'status',
        'created_at',
    )
    list_filter = ('status', 'current_stage')
    search_fields = ('design_request__title', 'vendor__company_name', 'client__email')
    inlines = [ProductionUpdateInline]


@admin.register(ProductionUpdate)
class ProductionUpdateAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'stage', 'created_by', 'created_at')
    list_filter = ('stage',)
