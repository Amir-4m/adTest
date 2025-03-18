from rest_framework import mixins, generics, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.authentication.authentications import CustomAuthentication
from apps.users.api.serializers import UserSerializer
from apps.users.models import User


class UserView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (CustomAuthentication,)
    permission_classes = (IsAuthenticated,)
    # throttle_classes = (SendEmailThrottle,)
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_active=True)

    def get_object(self):
        self.request.user.refresh_from_db()
        return self.request.user

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
