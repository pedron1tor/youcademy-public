import io
import os
from urllib.parse import urlparse
from pathlib import Path
import environ
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import redis
from django.core.exceptions import ImproperlyConfigured
# Import the original settings from each template
from .basesettings import *

# Load the settings from the environment variable
env = environ.Env()
env.read_env(io.StringIO(os.environ.get("APPLICATION_SETTINGS", None)))
PROD = True if env(
    'DJANGO_SETTINGS_MODULE') == 'mainframe.settings.prod' else False
OPENAI_KEY = env('OPENAI_KEY')
# Setting this value from django-environ
SECRET_KEY = env("SECRET_KEY")
uri = env('MONGO_URI')

client = MongoClient(uri, server_api=ServerApi('1'))

try:
  client.admin.command('ping')
  print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
  print(e)
MDB = client.youcademywriting
MDB_1 = client.reading
if "mainframe" not in INSTALLED_APPS:
  INSTALLED_APPS.append("mainframe")
# If defined, add service URL to Django security settings
CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)
if CLOUDRUN_SERVICE_URL:
  ALLOWED_HOSTS = [
      urlparse(CLOUDRUN_SERVICE_URL).netloc, 'youcademy.dev',
      'www.youcademy.dev'
  ]
  CSRF_TRUSTED_ORIGINS = [
      CLOUDRUN_SERVICE_URL,
      'https://youcademy.dev',
  ]
else:
  ALLOWED_HOSTS = ["*"]

# Default false. True allows default landing pages to be visible
DEBUG = env("DEBUG", default=False)

# Set this value from django-environ
DATABASES = {"default": env.db()}

if os.getenv("USE_CLOUD_SQL_AUTH_PROXY", None):
  DATABASES["default"]["HOST"] = "127.0.0.1"
  DATABASES["default"]["PORT"] = 5432

REDIS_IP = env('REDISHOST')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_IP, 6379)],
        },
    },
}
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_IP}:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


def check_redis_connection(host, port):
  try:
    client = redis.StrictRedis(host=host, port=port)
    client.ping()
    print("Pinged your deployment. You successfully connected to Redis!")
  except (redis.ConnectionError, redis.TimeoutError) as e:
    print(f"Cannot connect to Redis at {host}:{port}. Error: {e}")


check_redis_connection(REDIS_IP, 6379)
# Define static storage via django-storages[google]
GS_BUCKET_NAME = env("GS_BUCKET_NAME")
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
DEFAULT_FILE_STORAGE = 'mainframe.cloudstorage.CustomGoogleCloudStorage'
GS_DEFAULT_ACL = "publicRead"
# Application URL
URL = "https://youcademy.dev"
WS_URL = "wss://youcademy.dev/ws/chat/"
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
