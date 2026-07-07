from django.contrib import admin

from apps.disputes.models import Dispute


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'raised_by',
        'reason',
        'status',
        'resolved_by',
        'created_at',
    )
    list_filter = ('status',)
    search_fields = ('reason', 'raised_by__email')
