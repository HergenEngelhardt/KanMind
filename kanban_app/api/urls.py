from django.urls import path
from .views import (
    BoardListCreateView,
    BoardDetailView,
    EmailCheckView,
    ColumnListCreateView,
    ColumnDetailView,
)

"""
Kanban API URL patterns.

Provides endpoints for:
- Board management (CRUD operations)
- Column management within boards
- User email verification for board membership
"""

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list-create"),
    path("boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path("boards/<int:board_id>/columns/",ColumnListCreateView.as_view(),name="column-list-create",),
    path("columns/<int:pk>/", ColumnDetailView.as_view(), name="column-detail"),
]