import base64

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class BasicAuthMixin:
    """
    Mixin to enforce Basic Authentication on APIView classes.
    """
    VALID_USERNAME = settings.ADYEN_BASIC_USERNAME
    VALID_PASSWORD = settings.ADYEN_BASIC_PASSWORD

    def enforce_basic_auth(self, request):
        # Get the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', request.META.get('headers', {}).get('Authorization'))
        if not auth_header or not auth_header.startswith('Basic '):
            raise AuthenticationFailed('Authorization header missing or incorrect')

        # Decode the Base64 encoded credentials
        try:
            encoded_credentials = auth_header.split(' ')[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':')
        except (IndexError, ValueError, base64.binascii.Error):
            raise AuthenticationFailed('Invalid Basic Auth credentials')

        # Validate the credentials
        if username != self.VALID_USERNAME or password != self.VALID_PASSWORD:
            raise AuthenticationFailed('Invalid username or password')

    def perform_authentication(self, request):
        self.enforce_basic_auth(request)
        return super().perform_authentication(request)
