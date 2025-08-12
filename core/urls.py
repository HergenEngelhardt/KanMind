"""
KanMind API URL Configuration.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('kanban_app.api.urls')),
    path('api/', include('tasks_app.api.urls')),
]