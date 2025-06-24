from django.urls import path
from .views import (
    BoardListCreateView,
    BoardDetailView,
    EmailCheckView,
    ColumnListCreateView,
    ColumnDetailView,
)

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list-create"),
    path("boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path(
        "email-check/", EmailCheckView.as_view(), name="email-check"
    ),  # Changed from check-email
    path(
        "boards/<int:board_id>/columns/",
        ColumnListCreateView.as_view(),
        name="column-list-create",
    ),
    path("columns/<int:pk>/", ColumnDetailView.as_view(), name="column-detail"),
]
