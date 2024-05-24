from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Endpoint

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('API-Key')
        if not api_key:
            return None

        try:
            endpoint = Endpoint.objects.get(api_key=api_key)
        except Endpoint.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')

        return (endpoint.user, None)
