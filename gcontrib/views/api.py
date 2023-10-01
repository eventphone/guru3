import json

from django.conf import settings
from django.http.response import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from jsonschema import validate, ValidationError


class JsonError(Exception):
    def __init__(self, error_msg: str):
        self.error_msg = error_msg


class StaticJsonView(View):
    json_data = None
    pretty = False

    def get(self, _request, *_args, **_kwargs):
        if self.pretty:
            return JsonResponse(self.json_data, json_dumps_params={"indent": 4, "sort_keys": True})
        else:
            return JsonResponse(self.json_data)


@method_decorator(csrf_exempt, name="dispatch")
class JsonApiView(View):
    json_schema = None

    def validate_json_schema(self, data):
        if self.json_schema is None:
            return

        # we want $id to be settable in a dynamic way so that we can use reverse_lazy to push django urls
        self.json_schema["$id"] = str(self.json_schema.get("$id"))
        try:
            validate(instance=data, schema=self.json_schema)
        except ValidationError as e:
            raise JsonError(f"JSONSchema validation failed: {e}") from e

    @staticmethod
    def parse_json_input(request):
        if request.content_type != "application/json":
            raise JsonError("Request must be application/json")

        if request.body is None or request.body == b"":
            raise JsonError("No content")
        try:
            body_data = request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
        except UnicodeDecodeError:
            raise JsonError(f"Charset parsing error. Either specify encoding. Otherwise, we expect: "
                            f"{settings.DEFAULT_CHARSET}")
        try:
            return json.loads(body_data)
        except json.JSONDecodeError as e:
            raise JsonError("Invalid JSON") from e

    def json_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def process_get(self, request):
        return self.http_method_not_allowed(request)

    def get(self, request, *_args, **_kwargs):
        return self.process_get(request)

    def process_post(self, request, json_data):
        return self.http_method_not_allowed(request)

    def post(self, request, *_args, **_kwargs):
        # to ensure that we do not get back into CSRF scenarios, we enforce API key authentication
        if not request.api_key_authentication:
            return HttpResponseForbidden("This can only be used via API key.")
        try:
            json_data = self.parse_json_input(request)
            self.validate_json_schema(json_data)
        except JsonError as e:
            return HttpResponseBadRequest(e.error_msg)
        return self.process_post(request, json_data)

    def process_put(self, request, json_data):
        return self.http_method_not_allowed(request)

    def put(self, request, *_args, **_kwargs):
        # to ensure that we do not get back into CSRF scenarios, we enforce API key authentication
        if not request.api_key_authentication:
            return HttpResponseForbidden("This can only be used via API key.")
        try:
            json_data = self.parse_json_input(request)
            self.validate_json_schema(json_data)
        except JsonError as e:
            return HttpResponseBadRequest(e.error_msg)
        return self.process_put(request, json_data)

    def process_delete(self, request):
        return self.http_method_not_allowed(request)

    def delete(self, request, *_args, **_kwargs):
        # to ensure that we do not get back into CSRF scenarios, we enforce API key authentication
        if not request.api_key_authentication:
            return HttpResponseForbidden("This can only be used via API key.")
        return self.process_delete(request)

