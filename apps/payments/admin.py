from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'brand',
        'campaign',
        'ad',
        'amount',
        'transaction_type',
        'cost_type',
        'created_at'
    )
    list_filter = ('transaction_type', 'cost_type', 'brand')
    search_fields = (
        'brand__name',
        'campaign__name',
        'ad__name'
    )
    ordering = ('-created_at',)
