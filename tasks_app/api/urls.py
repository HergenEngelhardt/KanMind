from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TaskViewSet
from .comment_views import CommentListCreateView, CommentDetailView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
    path('tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('tasks/<int:task_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]