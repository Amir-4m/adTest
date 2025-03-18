from django.contrib import admin
from .models import UserVerificationRequest
from djangoql.admin import DjangoQLSearchMixin


@admin.action(description='Make selected requests verified')
def verify_request(modeladmin, request, queryset):
    queryset.update(used=True, is_active=False)


@admin.register(UserVerificationRequest)
class UserVerificationRequestAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'uuid', 'code', 'email',
        'user', 'used', 'is_active',
        'created_at', 'updated_at'
    )
    search_fields = ('email', 'code')
    list_filter = ('used',)
    raw_id_fields = ('user',)
    actions = [verify_request]
