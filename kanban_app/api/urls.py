from django.urls import path
from . import views

"""
Kanban API URL patterns.

Provides endpoints for:
- Board management (CRUD operations)
- Column management within boards
- User email verification for board membership
"""

urlpatterns = [
    path("", views.BoardListCreateView.as_view(), name="board-list-create"),
    path("<int:pk>/", views.BoardDetailView.as_view(), name="board-detail"),
    path("<int:pk>/members/", views.BoardMembersView.as_view(), name="board-members"),
    path("email-check/", views.EmailCheckView.as_view(), name="email-check"),
    path("<int:board_id>/columns/", views.ColumnListCreateView.as_view(), name="column-list-create"),
    path("columns/<int:pk>/", views.ColumnDetailView.as_view(), name="column-detail"),
    path("tasks/reorder/", views.TaskReorderView.as_view(), name="task-reorder"),
]