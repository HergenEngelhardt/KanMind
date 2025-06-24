from django.urls import path
from . import views

urlpatterns = [
    path("", views.TaskListCreate.as_view(), name="task-list-create"),
    path("<int:pk>/", views.TaskRetrieveUpdateDestroy.as_view(), name="task-detail"),
    path(
        "assigned-to-me/",
        views.TasksAssignedToMeView.as_view(),
        name="tasks-assigned-to-me",
    ),
    path("reviewing/", views.TasksReviewingView.as_view(), name="tasks-reviewing"),
    path(
        "<int:task_id>/comments/",
        views.CommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "<int:task_id>/comments/<int:pk>/",
        views.CommentDeleteView.as_view(),
        name="comment-delete",
    ),
]
