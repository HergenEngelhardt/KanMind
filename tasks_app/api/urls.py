from django.urls import path
from .views import TaskViewSet
from .comment_views import CommentListCreateView, CommentDetailView

urlpatterns = [
    path('tasks/assigned-to-me/', TaskViewSet.as_view({'get': 'assigned_to_me'}), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', TaskViewSet.as_view({'get': 'reviewing'}), name='tasks-reviewing'),
    path('tasks/', TaskViewSet.as_view({'get': 'list', 'post': 'create'}), name='task-list-create'),
    path('tasks/<int:pk>/', TaskViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='task-detail'),
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]