from rest_framework import routers

from .views import CampaignViewSet, AdViewSet, BrandViewSet, AdSetViewSet

router = routers.DefaultRouter()
router.register('campaigns', CampaignViewSet, basename='campaigns-api')
router.register('ads', AdViewSet, basename='ads-api')
router.register('ad-sets', AdSetViewSet, basename='ad-sets-api')
router.register('brands', BrandViewSet, basename='brands-api')

urlpatterns = []

urlpatterns += router.urls
