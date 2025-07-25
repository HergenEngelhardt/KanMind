"""
URL configuration for authentication API endpoints.

This module defines URL patterns for user authentication related views
including login, registration, and email validation.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registration/', views.registration_view, name='registration'),
    path('email-check/', views.email_check, name='email-check'),
]