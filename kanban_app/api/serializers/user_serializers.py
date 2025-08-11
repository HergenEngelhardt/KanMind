"""
User serializer module for the Kanban API.

This module contains serializers for user-related operations.
"""

from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user representation.
    
    Provides basic user information with a computed full name.
    
    Args:
        serializers.ModelSerializer: DRF base serializer class
    """
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'fullname')
    
    def get_fullname(self, obj):
        """
        Compute the full name of the user.
        
        Args:
            obj (User): User object
            
        Returns:
            str: Full name or username if no name is set
        """
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or obj.username