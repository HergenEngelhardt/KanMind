"""
Main URL configuration for KanMind project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('kanban_app.api.urls')),
    path('api/', include('tasks_app.api.urls')),
]