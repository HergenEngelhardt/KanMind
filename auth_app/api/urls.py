from django.urls import path
from .registration_views import RegisterView
from .login_views import LoginView
from .guest_views import GuestLoginView
"""
Authentication API URL patterns.

Provides endpoints for:
- User registration with token creation
- User login with email or username
- Guest access for demo purposes
"""

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
]