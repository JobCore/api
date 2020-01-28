from django.db import IntegrityError
from django.http import HttpResponseBadRequest

import json
import logging

log = logging.getLogger('api.middleware')


class ValueErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.

        return response

    def process_exception(self, request, exception):
        log.debug(f"{request}: {exception}")
        if isinstance(exception, ValueError):
            return HttpResponseBadRequest(content_type='application/json',
                                          content=json.dumps({"error": str(exception)}))
