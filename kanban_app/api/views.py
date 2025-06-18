from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from kanban_app.models import Board
from kanban_app.api.serializers import BoardListSerializer, BoardDetailSerializer, UserSerializer
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
        if self.request.method == 'POST':
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
        if self.request.method == 'DELETE':
            return [IsOwner()]
        return [IsOwnerOrMember()]

    def get_queryset(self):
        return Board.objects.all()

    def partial_update(self, request, *args, **kwargs):
        allowed_fields = {'title', 'members'}

        if not all(field in allowed_fields for field in request.data.keys()):
            return Response(
                {"error": "Only the fields 'title' and 'members' can be edited."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = super().partial_update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            if 'owner_id' in response.data:
                del response.data['owner_id']
                del response.data['tasks']
            response.data['owner_data'] = UserSerializer(
                self.get_object().owner_id).data

            if 'members' in response.data:
                response.data['members_data'] = response.data.pop('members')

        return response

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return Response(
            {"message": f"board successfully deleted."},
            status=status.HTTP_204_NO_CONTENT
        )


class EmailCheckView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            id = user.id
            email = user.email
            fullname = user.fullname
            return Response({"id": id, "email": email, "fullname": fullname}, status=status.HTTP_200_OK)
        return Response({"exists": False}, status=status.HTTP_404_NOT_FOUND)