from django.urls import path

from . import views

urlpatterns = [
 path("signup", views.signup, name="signup"),
 path("login", views.login, name="login"),
 path("logout", views.logout, name="logout"),
 path("research", views.purchase, name="purchase"),
 path("aipolicy", views.aipolicy, name="aipolicy"),
 path("onboard", views.onboard, name="onboard")
]