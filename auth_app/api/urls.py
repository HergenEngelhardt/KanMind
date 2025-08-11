"""
URL configuration for authentication API endpoints.

Defines URL patterns for authentication operations.
"""
from django.urls import path
from rest_framework.permissions import AllowAny
from .views import RegistrationView, LoginView, EmailCheckView

class PublicRegistrationView(RegistrationView):
    authentication_classes = []
    permission_classes = [AllowAny]

class PublicLoginView(LoginView):
    authentication_classes = []
    permission_classes = [AllowAny]

class PublicEmailCheckView(EmailCheckView):
    authentication_classes = []
    permission_classes = [AllowAny]

urlpatterns = [
    path('registration/', PublicRegistrationView.as_view(), name='registration'),
    path('login/', PublicLoginView.as_view(), name='login'),
    path('email-check/', PublicEmailCheckView.as_view(), name='email-check'),
]