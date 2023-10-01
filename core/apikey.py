from django.conf import settings

from core.models import UserApiKey


class ApiKeyAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.api_key_authentication = False
        if request.path.startswith("/api/"):
            key_obj = None
            api_key_header = "HTTP_" + settings.AUTH_KEY_HEADER.upper()
            if api_key_header in request.META:
                api_key = request.META[api_key_header]
                split_key = api_key.split("$", 1)
                if len(split_key) == 2 and split_key[0].isnumeric():
                    try:
                        key_obj = UserApiKey.objects.get(user=split_key[0])
                    except UserApiKey.DoesNotExist:
                        pass
            if key_obj is not None and key_obj.check_apikey(split_key[1]):
                request.user = key_obj.user
                request.api_key_authentication = True
        response = self.get_response(request)

        return response
