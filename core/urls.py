"""
Main URL configuration for KanMind project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def test_view(request):
    return Response({"message": "API is working!", "method": request.method})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/test/', test_view, name='test-view'),  # Add this test endpoint
    path('api/', include('auth_app.api.urls')),
    path('api/', include('kanban_app.api.urls')),
    path('api/', include('tasks_app.api.urls')),
]