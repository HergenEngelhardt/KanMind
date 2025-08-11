"""
URL configuration for authentication API endpoints.

Defines URL patterns for authentication operations.
"""
from django.urls import path
from .views import RegistrationView, LoginView, EmailCheckView

urlpatterns = [
    path('registration/', RegistrationView.as_view(), name='registration'),
    path('login/', LoginView.as_view(), name='login'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]