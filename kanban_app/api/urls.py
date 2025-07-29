from django.urls import path
from .views.board_views import BoardViewSet

urlpatterns = [
    path('boards/', BoardViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='boards-list'),
    path('boards/<int:pk>/', BoardViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='boards-detail'),
]