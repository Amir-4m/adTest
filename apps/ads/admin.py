from django.contrib import admin
from .models import Ad, AdSet, GlobalAdPricing, Brand, Campaign


@admin.register(GlobalAdPricing)
class GlobalAdPricingAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'cost_per_click', 'cost_per_impression', 'cost_per_view', 'cost_per_acquisition')
    search_fields = ('uuid',)
    ordering = ('uuid',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'daily_budget', 'monthly_budget', 'timezone_str', 'owner', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'owner__username')
    ordering = ('name',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'brand', 'status', 'allowed_start_hour', 'allowed_end_hour')
    list_filter = ('status', 'brand')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(AdSet)
class AdSetAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'name', 'campaign', 'is_active')
    list_filter = ('campaign', 'is_active')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'name',
        'adset',
        'is_active',
        'cost_per_click',
        'cost_per_impression',
        'cost_per_view',
        'cost_per_acquisition'
    )
    list_filter = ('adset', 'is_active')
    search_fields = ('name',)
    ordering = ('name',)
