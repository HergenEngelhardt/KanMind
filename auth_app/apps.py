from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """
    Configuration for the authentication app.
    
    Handles user registration, login, and authentication-related functionality.
    Provides token-based authentication for API access.
    """
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"