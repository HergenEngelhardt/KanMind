"""
URL configuration for authentication API.

This module defines the URL patterns for authentication-related endpoints.
"""
from django.urls import path
from .views import RegistrationView, LoginView, GuestLoginView

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('guest-login/', GuestLoginView.as_view(), name='guest-login'),
]