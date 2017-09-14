from google.appengine.api import users

from django.http import HttpResponseForbidden


class PotatoLodingMiddleware(object):
    def process_request(self, request):
        if not users.get_current_user().email().endswith('@potatolondon.com'):
            return HttpResponseForbidden()
