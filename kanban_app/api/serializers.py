from rest_framework import serializers
from kanban_app.models import Board, BoardMembership, Column
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class BoardListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'owner', 'created_at', 'updated_at']


class BoardMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BoardMembership
        fields = ['id', 'user', 'role']


class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['id', 'name', 'position']


class BoardDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(source='boardmembership_set', many=True, read_only=True)
    columns = ColumnSerializer(many=True, read_only=True)
    
    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'owner', 'members', 'columns', 'created_at', 'updated_at']