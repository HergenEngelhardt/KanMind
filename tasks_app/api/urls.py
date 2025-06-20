from django.urls import path
from . import views

urlpatterns = [
    path('', views.TaskListCreate.as_view(), name='task-list-create'),
    path('<int:pk>/', views.TaskRetrieveUpdateDestroy.as_view(), name='task-detail'),
]