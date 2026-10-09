import io
import os
from urllib.parse import urlparse

# Import the original settings from each template
from .basesettings import *
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Load the settings from the environment variable

from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv('DEBUG')
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
uri = os.getenv('MONGO_URI')

client = MongoClient(uri, server_api=ServerApi('1'))

try:
  client.admin.command('ping')
  print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
  print(e)
MDB = client.youcademywriting
MDB_1 = client.reading
PROD = True if os.getenv(
    'DJANGO_SETTINGS_MODULE') == 'mainframe.settings.prod' else False
# If you have global static files, not tied to any particular app
STATICFILES_DIRS = [
    os.path.join(BASE_DIR,
                 'static'),  # This line is needed to define the location
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
OPENAI_KEY = os.getenv('OPENAI_KEY')
# Setting this value from django-environ
SECRET_KEY = os.getenv("SECRET_KEY")
ALLOWED_HOSTS = ["*"]
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# Google Cloud Storage settings (disabled for local development)
# DEFAULT_FILE_STORAGE = 'mainframe.cloudstorage.CustomGoogleCloudStorage'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# GS_PROJECT_ID = 'your-gcp-project-id'
# GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
URL = "http://localhost:8000"
WS_URL = "ws://127.0.0.1:8000/ws/chat/"

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    # Add other trusted origins if needed
]

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    # Add other allowed hosts if needed
]
