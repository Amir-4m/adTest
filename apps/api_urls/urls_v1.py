from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

schema_view = get_schema_view(
    openapi.Info(
        title="AD Agency API",
        default_version='v1',
        description="AD Agency V1 APIs documentation."
    ),
    urlconf="adTest.urls",
    public=False,
    authentication_classes=[SessionAuthentication, BasicAuthentication],
    permission_classes=[permissions.IsAdminUser],

)
urlpatterns = [
    path('auth/', include('apps.authentication.api.urls')),
    path('user/', include('apps.users.api.urls')),
    path('ads/', include('apps.ads.api.urls')),
    path('docs', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(
        r'^docs(?P<format>\.json)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
    ),
]
