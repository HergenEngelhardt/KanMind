"""
URL configuration for board API endpoints.
"""
from django.urls import path
from .views.board_views import BoardViewSet
from .views.column_views import ColumnListCreateView, ColumnDetailView

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
    path('boards/<int:board_id>/columns/', 
         ColumnListCreateView.as_view(), 
         name='board-columns-list'),
    path('columns/<int:pk>/', 
         ColumnDetailView.as_view(), 
         name='column-detail'),
]