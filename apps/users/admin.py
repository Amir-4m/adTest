from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email',
        'phone_number', 'gender',
        'is_active', 'created_at', 'updated_at',

    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'logo')}),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')
    list_filter = ('is_active', 'gender')
    filter_horizontal = ('groups',)
