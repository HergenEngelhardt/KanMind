"""URL patterns for the kanban app API.

This module defines URL patterns for board and column management.
"""

from django.urls import path
from .views import (
    BoardListCreateView, 
    BoardDetailView,
    ColumnListCreateView, 
    ColumnDetailView,
    EmailCheckView
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),
    path('boards/<int:board_id>/columns/', ColumnListCreateView.as_view(), name='column-list-create'),
    path('boards/<int:board_id>/columns/<int:column_id>/', ColumnDetailView.as_view(), name='column-detail'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
]