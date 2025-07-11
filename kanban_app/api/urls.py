from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.board_views import (
    BoardViewSet
)
from .views.column_views import (
    ColumnListCreateView,
    ColumnDetailView
)
from .views.utils_views import (
    EmailCheckView,
)

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')

urlpatterns = [
    path('', include(router.urls)),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
    path('<int:board_id>/columns/', ColumnListCreateView.as_view(), name='column-list-create'),
    path('<int:board_id>/columns/<int:pk>/', ColumnDetailView.as_view(), name='column-detail'),
]