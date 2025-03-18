from django.urls import path
from rest_framework import routers

from .views import UserView

router = routers.DefaultRouter()

urlpatterns = [
    path('', UserView.as_view(), name='user-api'),
]

urlpatterns += router.urls
