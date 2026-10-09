from django.apps import AppConfig
from api.tasks import start_background_task


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"