from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.ads.models import Campaign, AdSet, Ad, Brand


class BrandSerializer(serializers.ModelSerializer):
    __doc__ = _("""
               Brand serializer.
           """)

    class Meta:
        model = Brand
        fields = '__all__'


class CampaignSerializer(serializers.ModelSerializer):
    __doc__ = _("""
               Campaigns serializer.
           """)

    class Meta:
        model = Campaign
        fields = '__all__'

    def validate(self, attrs):
        user = self.context['request'].user
        brand = attrs['brand']
        if brand.owner != user:
            raise serializers.ValidationError(
                _("invalid.")
            )
        allowed_start = attrs.get('allowed_start_hour')
        allowed_end = attrs.get('allowed_end_hour')
        if allowed_start and allowed_end:
            if allowed_start == allowed_end:
                raise serializers.ValidationError(
                    _("Allowed start and end hours cannot be the same.")
                )
        return attrs


class AdSetSerializer(serializers.ModelSerializer):
    __doc__ = _("""
               AdSet serializer.
           """)

    class Meta:
        model = AdSet
        fields = '__all__'

    def validate(self, attrs):
        user = self.context['request'].user
        campaign = attrs['campaign']
        if campaign.brand.owner != user:
            raise serializers.ValidationError(
                _("invalid.")
            )
        return attrs


class AdSerializer(serializers.ModelSerializer):
    __doc__ = _("""
               Ad serializer.
           """)

    class Meta:
        model = Ad
        fields = '__all__'

    def validate(self, attrs):
        user = self.context['request'].user
        adset = attrs['adset']
        if adset.campaign.brand.owner != user:
            raise serializers.ValidationError(
                _("invalid.")
            )
        return attrs
