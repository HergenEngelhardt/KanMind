from rest_framework import serializers
from django.contrib.auth.models import User
from tasks_app.api.serializers import TaskSerializer, UserSerializer
from kanban_app.models import Board, BoardMembership, Column


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for board list view.
    
    Provides basic board information for listing purposes.
    Includes owner details but excludes detailed relationships.
    """
    
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Board
        fields = [
            "id", 
            "name", 
            "description", 
            "owner", 
            "created_at", 
            "updated_at"
        ]


class BoardMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for board membership relationships.
    
    Represents user roles within a board.
    Used for displaying board members and their permissions.
    """
    
    user = UserSerializer(read_only=True)

    class Meta:
        model = BoardMembership
        fields = ["id", "user", "role"]


class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for board columns.
    
    Includes associated tasks for complete column representation.
    Board field is read-only to prevent unauthorized modifications.
    """
    
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Column
        fields = ["id", "name", "position", "board", "tasks"]
        read_only_fields = ["board"]

    def validate_position(self, value):
        """
        Validate column position is positive.
        
        Args:
            value (int): Position value
            
        Returns:
            int: Validated position
            
        Raises:
            ValidationError: If position is not positive
        """
        if value < 1:
            raise serializers.ValidationError(
                "Position must be a positive integer."
            )
        return value


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual board view.
    
    Includes complete board information with members, columns, and tasks.
    Used for board detail and edit operations.
    """
    
    owner = UserSerializer(read_only=True)
    members = BoardMembershipSerializer(
        source="boardmembership_set", 
        many=True, 
        read_only=True
    )
    columns = ColumnSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "members",
            "columns",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        """
        Validate board name is not empty.
        
        Args:
            value (str): Board name
            
        Returns:
            str: Validated name
            
        Raises:
            ValidationError: If name is empty or whitespace only
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Board name cannot be empty."
            )
        return value.strip()