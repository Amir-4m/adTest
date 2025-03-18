from functools import lru_cache

from django.utils.translation import gettext_lazy as _

from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings

from apps.users.models import User


class CustomAuthentication(JWTAuthentication):
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        payload = {}
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        if not validated_token:  # no id passed in request headers
            raise exceptions.AuthenticationFailed(_('No such company user'))  # authentication did not succeed
        user_pk = validated_token.get(api_settings.USER_ID_CLAIM)

        if user_pk:
            try:
                user = self.authenticate_credentials(user_pk=user_pk)  # get the page
            except Exception:
                raise exceptions.AuthenticationFailed('No such user')  # raise exception if user does not exist
            return user, payload  # authentication successful

        raise exceptions.AuthenticationFailed('Token is expired!')

    @staticmethod
    @lru_cache(maxsize=None)
    def authenticate_credentials(user_pk=None):
        """
        Returns a user of the existing service
        """
        if not user_pk:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)

        if user_pk:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                msg = _('Invalid signature.')
                raise exceptions.AuthenticationFailed(msg)
            except Exception as e:
                raise exceptions.AuthenticationFailed(e)
            return user
