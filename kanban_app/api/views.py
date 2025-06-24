from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied, NotFound
from kanban_app.models import Board, Column
from tasks_app.models import Task
from kanban_app.api.serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    UserSerializer,
    ColumnSerializer,
)
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from kanban_app.api.permissions import IsOwnerOrMember, IsOwner
from django.db import models
from django.contrib.auth.models import User


class BoardListCreateView(ListCreateAPIView):
    serializer_class = BoardListSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(
            models.Q(owner_id=user) | models.Q(members=user)
        ).distinct()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsOwnerOrMember()]

    def perform_create(self, serializer):
        board = serializer.save(owner_id=self.request.user)
        if not board.members.filter(id=self.request.user.id).exists():
            board.members.add(self.request.user)


class BoardDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = BoardDetailSerializer
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method == "DELETE":
            return [IsOwner()]
        return [IsOwnerOrMember()]

    def get_queryset(self):
        return Board.objects.all()

    def partial_update(self, request, *args, **kwargs):
        allowed_fields = {"name", "members"}

        if not all(field in allowed_fields for field in request.data.keys()):
            return Response(
                {"error": "Only the fields 'name' and 'members' can be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = super().partial_update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            if "owner_id" in response.data:
                del response.data["owner_id"]

            response.data["owner_data"] = UserSerializer(self.get_object().owner).data

            if "members" in response.data:
                response.data["members_data"] = response.data.pop("members")

        return response

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return Response(
            {"message": f"board successfully deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )


class EmailCheckView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get("email")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            return Response(
                {
                    "id": user.id,
                    "email": user.email,
                    "fullname": f"{user.first_name} {user.last_name}",
                },
                status=status.HTTP_200_OK,
            )
        return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)


class ColumnListCreateView(generics.ListCreateAPIView):
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        board_id = self.kwargs.get("board_id")
        return Column.objects.filter(board_id=board_id)

    def perform_create(self, serializer):
        board_id = self.kwargs.get("board_id")
        try:
            board = Board.objects.get(pk=board_id)
            if not IsOwnerOrMember().has_object_permission(self.request, self, board):
                raise PermissionDenied(
                    "You don't have permission to add columns to this board"
                )
            serializer.save(board=board)
        except Board.DoesNotExist:
            raise NotFound("Board not found")


class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ColumnSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrMember]

    def get_queryset(self):
        return Column.objects.all()


class TaskReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        task_id = request.data.get("task_id")
        column_id = request.data.get("column_id")
        position = request.data.get("position")

        try:
            task = Task.objects.get(id=task_id)
            column = Column.objects.get(id=column_id)

            if not (
                task.column.board.owner == request.user
                or request.user in task.column.board.members.all()
            ):
                raise PermissionDenied("You don't have permission to modify this task")

            old_column = task.column
            old_position = task.position

            task.column = column
            task.position = position
            task.save()

            if old_column == column:
                if old_position < position:
                    Task.objects.filter(
                        column=column, position__gt=old_position, position__lte=position
                    ).exclude(id=task_id).update(position=models.F("position") - 1)
                elif old_position > position:
                    Task.objects.filter(
                        column=column, position__gte=position, position__lt=old_position
                    ).exclude(id=task_id).update(position=models.F("position") + 1)
            else:
                Task.objects.filter(
                    column=old_column, position__gt=old_position
                ).update(position=models.F("position") - 1)

                Task.objects.filter(column=column, position__gte=position).exclude(
                    id=task_id
                ).update(position=models.F("position") + 1)

            return Response({"success": True}, status=status.HTTP_200_OK)
        except (Task.DoesNotExist, Column.DoesNotExist):
            return Response(
                {"error": "Task or column not found"}, status=status.HTTP_404_NOT_FOUND
            )
