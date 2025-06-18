from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardListCreateView, BoardDetailView 


urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:pk>/', BoardDetailView.as_view(), name='board-detail'),
]