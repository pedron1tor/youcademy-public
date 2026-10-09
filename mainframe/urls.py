"""mainframe URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from pages.views import home
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from django.urls import re_path
from django.views.static import serve
from django.conf.urls import handler500
from pages import views

handler500 = 'pages.views.custom_500_view'  
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("pages/", include("pages.urls")),
    path("teacher/", include("teacher.urls"), name='student_home'),
    path("student/", include("student.urls")),
    path('api/', include('api.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('allauth.socialaccount.urls')),

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#TODO REFACTOR WHEN DEPLOYING TO PRODUCTION...
if not settings.PROD:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    