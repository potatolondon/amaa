from google.appengine.api import users

from amaa.settings import GOOGLE_APPS_EMAIL_DOMAIN
from django.http import HttpResponseForbidden


class PotatoAuthMiddleware(object):
    def process_request(self, request):
        if users.get_current_user() is not None and not users.get_current_user().email().endswith('@{}'.format(GOOGLE_APPS_EMAIL_DOMAIN)):
            return HttpResponseForbidden()
