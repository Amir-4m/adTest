from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from apps.ads.api.serializers import CampaignSerializer, BrandSerializer, AdSerializer, AdSetSerializer
from apps.ads.models import Campaign, Brand, Ad, AdSet
from apps.authentication.authentications import CustomAuthentication


class BrandViewSet(viewsets.ModelViewSet):
    __doc__ = _("""
    API endpoint for Brand.
    """)
    serializer_class = BrandSerializer
    authentication_classes = (CustomAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Brand.objects.filter(is_active=True)
    search_fields = (
        'name',
    )
    ordering_fields = (
        'name', 'created_at', 'updated_at'
    )
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class CampaignViewSet(viewsets.ModelViewSet):
    __doc__ = _("""
    API endpoint for Campaigns.
    """)
    serializer_class = CampaignSerializer
    authentication_classes = (CustomAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Campaign.objects.filter(is_active=True)
    search_fields = (
        'name',
    )
    ordering_fields = (
        'name', 'status',
        'created_at', 'updated_at'
    )
    filterset_fields = ('brand', 'status')

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]

    def get_queryset(self):
        return super().get_queryset().filter(brand__owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class AdSetViewSet(viewsets.ModelViewSet):
    __doc__ = _("""
    API endpoint for AdSet.
    """)
    serializer_class = AdSetSerializer
    authentication_classes = (CustomAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = AdSet.objects.filter(is_active=True)
    search_fields = (
        'name',
    )
    ordering_fields = (
        'name', 'created_at', 'updated_at'
    )
    filterset_fields = ('campaign', 'campaign__brand')

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]

    def get_queryset(self):
        return super().get_queryset().filter(campaign__brand__owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class AdViewSet(viewsets.ModelViewSet):
    __doc__ = _("""
    API endpoint for Ad.
    """)
    serializer_class = AdSerializer
    authentication_classes = (CustomAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Ad.objects.filter(is_active=True)
    search_fields = (
        'name',
    )
    ordering_fields = (
        'name', 'created_at', 'updated_at'
    )
    filterset_fields = ('adset', 'adset__campaign', 'adset__campaign__brand')

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter
    ]

    def get_queryset(self):
        return super().get_queryset().filter(adset__campaign__brand__owner=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
