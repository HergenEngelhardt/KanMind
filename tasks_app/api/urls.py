from django.urls import path
from .task_views import (
    TaskListCreate,
    TaskRetrieveUpdateDestroy,
    TasksAssignedToMeView,
    TasksReviewingView
)
from .comment_views import (
    CommentListCreateView,
    CommentDeleteView
)

urlpatterns = [

    path('tasks/', TaskListCreate.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskRetrieveUpdateDestroy.as_view(), name='task-detail'),
    path('tasks/assigned-to-me/', TasksAssignedToMeView.as_view(), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', TasksReviewingView.as_view(), name='tasks-reviewing'),
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:pk>/', CommentDeleteView.as_view(), name='comment-delete'),
]