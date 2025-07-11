from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth.models import User

from kanban_app.models import Board, BoardMembership
from kanban_app.api.serializers.board_serializers import (
    BoardListSerializer, 
    BoardDetailSerializer, 
    BoardCreateSerializer
)


class BoardViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BoardListSerializer
        elif self.action == 'create':
            return BoardCreateSerializer
        else:
            return BoardDetailSerializer
    
    def get_queryset(self):
        return Board.objects.filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).select_related('owner').prefetch_related(
            'members',
            'columns',
            'columns__tasks',
            'columns__tasks__assignee',
            'columns__tasks__reviewers'
        ).distinct()

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception:
            return Response(
                {"error": "Board not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request, *args, **kwargs):
        print(f"DEBUG - Request data: {request.data}")  # Debug-Zeile hinzufügen
        print(f"DEBUG - Request content type: {request.content_type}")  # Debug-Zeile hinzufügen
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print(f"DEBUG - Serializer errors: {serializer.errors}")  # Debug-Zeile hinzufügen
            serializer.is_valid(raise_exception=True)
            board = serializer.save()
        
            response_serializer = BoardDetailSerializer(board, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"DEBUG - Exception: {str(e)}")  # Debug-Zeile hinzufügen
            return Response(
                {"error": "Could not create board"}, 
                status=status.HTTP_400_BAD_REQUEST
        )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            if instance.owner != request.user:
                return Response(
                    {"error": "Only board owners can update the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            data = request.data.copy()
            if 'members' in data:
                member_ids = data.pop('members')
                BoardMembership.objects.filter(board=instance).exclude(user=instance.owner).delete()
                
                for member_id in member_ids:
                    try:
                        user = User.objects.get(id=member_id)
                        if user != instance.owner:
                            BoardMembership.objects.get_or_create(
                                user=user,
                                board=instance,
                                defaults={'role': 'EDITOR'}
                            )
                    except User.DoesNotExist:
                        continue
            
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data)
        except Exception:
            return Response(
                {"error": "Could not update board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            
            if instance.owner != request.user:
                return Response(
                    {"error": "Only board owners can delete the board"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response(
                {"error": "Could not delete board"}, 
                status=status.HTTP_400_BAD_REQUEST
            )