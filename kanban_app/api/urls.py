from django.urls import path
from .views.board_views import (
    BoardListCreateView,
    BoardDetailView,
    BoardMembersView
)
from .views.column_views import (
    ColumnListCreateView,
    ColumnDetailView
)
from .views.utils_views import (
    EmailCheckView,
    TaskReorderView
)

"""
Kanban API URL patterns.

Provides endpoints for:
- Board management (CRUD operations)
- Column management within boards
- User email verification for board membership
"""

urlpatterns = [
    path("", BoardListCreateView.as_view(), name="board-list-create"),
    path("<int:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path("<int:pk>/members/", BoardMembersView.as_view(), name="board-members"),
    path("<int:board_id>/columns/", ColumnListCreateView.as_view(), name="column-list-create"),
    path("<int:board_id>/columns/<int:pk>/", ColumnDetailView.as_view(), name="column-detail"),
    path("check-email/", EmailCheckView.as_view(), name="check-email"),
    path("reorder-tasks/", TaskReorderView.as_view(), name="reorder-tasks"),
]