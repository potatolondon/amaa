from google.appengine.api import users

from amaa.settings import GOOGLE_APPS_EMAIL_DOMAIN
from django.http import HttpResponseForbidden


class PotatoAuthMiddleware(object):
    def process_request(self, request):
        from djangae import environment
        if environment.is_in_task():
            return

        if environment.is_in_cron():
            return

        if not users.get_current_user().email().endswith('@{}'.format(GOOGLE_APPS_EMAIL_DOMAIN)):
            return HttpResponseForbidden()
