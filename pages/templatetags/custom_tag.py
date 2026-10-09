# In a file named custom_tags.py in one of your app's templatetags directories

from django import template
from django.utils.translation import gettext as original_gettext
import json
import os
from django.conf import settings

register = template.Library()


def load_custom_translations():
    json_path = os.path.join(settings.BASE_DIR, "utils/translations.json")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Custom translations file not found at {json_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in custom translations file at {json_path}")
    return {}


custom_translations = load_custom_translations()


@register.simple_tag(takes_context=True)
def custom_trans(context, message):
    lang = context.get("LANGUAGE_CODE", settings.LANGUAGE_CODE)
    if lang in custom_translations and message in custom_translations[lang]:
        return custom_translations[lang][message]
    return original_gettext(message)
