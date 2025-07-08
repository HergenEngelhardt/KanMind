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
"""

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list-create"),
    path("boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path("boards/<int:pk>/members/", BoardMembersView.as_view(), name="board-members"),
    path("boards/email-check/", EmailCheckView.as_view(), name="email-check-boards"), 
    path("boards/<int:board_id>/columns/", ColumnListCreateView.as_view(), name="column-list-create"),
    path("boards/<int:board_id>/columns/<int:pk>/", ColumnDetailView.as_view(), name="column-detail"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path("reorder-tasks/", TaskReorderView.as_view(), name="reorder-tasks"),
]