from .task_views import (
    TaskViewSet,
    TaskListCreateView,
    TaskRetrieveUpdateDestroyView,
    TasksAssignedToMeView,
    TasksReviewingView
)
from .comment_views import (
    CommentListCreateView,
    CommentDetailView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from tasks_app.models import Task
from .serializers import TaskSerializer

class AssignedTasksView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(assignee=request.user)
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)

class ReviewingTasksView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(reviewers=request.user)
        serializer = TaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)

def assigned_to_me(request):
    view = AssignedTasksView.as_view()
    return view(request)

def reviewing(request):
    view = ReviewingTasksView.as_view()
    return view(request)

__all__ = [
    'TaskViewSet',
    'TaskListCreateView',
    'TaskRetrieveUpdateDestroyView', 
    'TasksAssignedToMeView',
    'TasksReviewingView',
    'CommentListCreateView',
    'CommentDetailView',
    'AssignedTasksView',
    'ReviewingTasksView',
    'assigned_to_me',
    'reviewing'
]