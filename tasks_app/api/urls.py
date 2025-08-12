"""
URL configuration for tasks API.

This module defines all URL patterns for task-related operations.
"""
from django.urls import path
from . import views
from . import comment_views

urlpatterns = [
    path('tasks/assigned-to-me/', views.AssignedTasksView.as_view(), name='assigned-tasks'),
    path('tasks/reviewing/', views.ReviewingTasksView.as_view(), name='reviewing-tasks'),
    path('tasks/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:task_id>/comments/', comment_views.CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:pk>/', comment_views.CommentDetailView.as_view(), name='comment-detail'),
    path('boards/<int:board_id>/tasks/', views.BoardTaskListView.as_view(), name='board-task-list'),
    path('boards/<int:board_id>/tasks/<int:pk>/', views.BoardTaskDetailView.as_view(), name='board-task-detail'),
]