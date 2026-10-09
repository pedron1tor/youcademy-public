
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django import http
from django.utils import timezone
import pytz

class DynamicHostMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host()
        if host == 'youcademy.dev':
            settings.URL = "https://youcademy.dev"
            settings.WS_URL = "wss://youcademy.dev/ws/chat/"
        elif host.startswith('localhost') or host.startswith('127.0.0.1'):
            settings.URL = "http://localhost:8000"
            settings.WS_URL = "ws://localhost:8000/ws/chat/"


class NoWWWRedirectMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host()
        if host.startswith('www.'):
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                no_www_host = host[4:]
                url = request.build_absolute_uri().replace(host, no_www_host, 1)
                return http.HttpResponsePermanentRedirect(url)
            
class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = None
        if request.user.is_authenticated:
            try:
                tzname = request.user.timezone  
            except AttributeError:
                # User model doesn't have timezone attribute
                pass

        if tzname:
            try:
                timezone.activate(pytz.timezone(tzname))
            except pytz.exceptions.UnknownTimeZoneError:
                # Invalid timezone name
                timezone.deactivate()
        else:
            timezone.deactivate()

        response = self.get_response(request)

        # Deactivate the timezone for the current thread
        timezone.deactivate()

        return response