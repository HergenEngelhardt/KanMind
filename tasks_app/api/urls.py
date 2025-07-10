from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet,
    TaskListCreateView,
    TaskRetrieveUpdateDestroyView,
    TasksAssignedToMeView,
    TasksReviewingView,
    CommentListCreateView,
    CommentDetailView,
    assigned_to_me,
    reviewing
)

router = DefaultRouter()
router.register(r'tasks-api', TaskViewSet, basename='task-api')

urlpatterns = [
    path('', include(router.urls)),
    
    path('assigned-to-me/', assigned_to_me, name='assigned-to-me'),
    path('reviewing/', reviewing, name='reviewing'),
    path('tasks/assigned-to-me/', TasksAssignedToMeView.as_view(), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', TasksReviewingView.as_view(), name='tasks-reviewing'),
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskRetrieveUpdateDestroyView.as_view(), name='task-detail'),
    
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]