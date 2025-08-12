"""URL patterns for the authentication API.

This module defines all URL patterns related to user authentication,
including registration, login, and guest access.
"""

from django.urls import path
from auth_app.api.views import (
    LoginView,
    RegistrationView,
    guest_login_view
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('guest-login/', guest_login_view, name='guest-login'),
    path('registration/', RegistrationView.as_view(), name='registration'),
]