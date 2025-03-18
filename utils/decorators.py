from django.core.cache import cache
from functools import wraps

from rest_framework.response import Response


def cache_response(timeout=60 * 15, cache_key=None):
    """
    A decorator that caches the response of a DRF method for a specified amount of time.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if cache_key:
                key = cache_key(*args, **kwargs)
            else:
                key = func.__name__ + str(args) + str(kwargs)
            cached_data = cache.get(key)
            if cached_data:
                return Response(cached_data['data'], status=cached_data['status'])
            response = func(*args, **kwargs)
            if not response.status_code == 200:
                return response
            data = response.data
            response_dict = {'data': data, 'status': response.status_code}
            cache.set(key, response_dict, timeout)
            return response

        return wrapper

    return decorator
