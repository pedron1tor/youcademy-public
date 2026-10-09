# In a new file, e.g., adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.account.utils import user_email, user_field, user_username
from allauth.utils import (
    deserialize_instance,
    import_attribute,
    serialize_instance,
    valid_email_or_none,
)
import logging
logger = logging.getLogger(__name__)
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
  def populate_user(self, request, sociallogin, data):
    logger.info(f"Populating user data: {data}")
    user = sociallogin.user
    
    # Log incoming data
    logger.debug(f"Incoming social data: {data}")

    # Handle name
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    full_name = data.get("name", f"{first_name} {last_name}".strip())
    user_field(user, "name", full_name or "Anonymous")
    
    # Handle email
    email = data.get("email")
    user_email(user, valid_email_or_none(email) or "")
    
    # Set default values for custom fields
    custom_fields = {
      "occupation": "Not specified",
      "diagnostic": False,
      "color": "#132143",
      "timezone": "UTC",
      "admin": False,
      "tour": False
    }
    
    for field, default_value in custom_fields.items():
      current_value = getattr(user, field, None)
      if current_value is None:
        user_field(user, field, default_value)
    
    logger.info(f"User populated: {user}")
    return user