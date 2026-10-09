from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/assessment/(?P<course_id>\w+)/$', consumers.AssessmentConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': SessionMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})