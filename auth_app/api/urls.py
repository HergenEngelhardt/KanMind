"""
URL configuration for authentication API endpoints.

This module defines URL patterns for user authentication related views
including login, registration, and email validation.
"""

from django.urls import path
from .views import registration_view, login_view, email_check

urlpatterns = [
    path('registration/', registration_view, name='api-registration'),
    path('login/', login_view, name='api-login'),
    path('email-check/', email_check, name='api-email-check'),
]