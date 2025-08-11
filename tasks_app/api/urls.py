"""
URL configuration for task API endpoints.

Defines URL patterns for task-related operations.
"""
from django.urls import path
from .views import (
    TaskViewSet, 
    TaskAssignedListView,
    TaskReviewingListView
)
from .comment_views import (
    TaskCommentListCreateView,
    TaskCommentDeleteView
)

urlpatterns = [
    path('tasks/assigned-to-me/', 
         TaskAssignedListView.as_view(), 
         name='tasks-assigned'),
    path('tasks/reviewing/', 
         TaskReviewingListView.as_view(), 
         name='tasks-reviewing'),
    path('tasks/', TaskViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='tasks-list'),
    path('tasks/<int:pk>/', TaskViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='task-detail'),
    path('tasks/<int:task_id>/comments/', 
         TaskCommentListCreateView.as_view(), 
         name='task-comments'),
    path('tasks/<int:task_id>/comments/<int:pk>/', 
         TaskCommentDeleteView.as_view(), 
         name='task-comment-delete'),
]