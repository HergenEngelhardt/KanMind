"""
User serializers module for the Kanban API.

This module contains serializers for user-related operations in the Kanban application.
"""

from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with additional fullname field.
    
    Provides serialization for Django's built-in User model with an additional
    computed fullname field that combines first_name and last_name.
    """
    
    fullname = serializers.SerializerMethodField()

    class Meta:
        """
        Meta configuration for UserSerializer.
        
        Defines the model, fields, and read-only fields for the serializer.
        """
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'fullname']
        read_only_fields = ['id']

    def get_fullname(self, obj):
        """
        Generate a fullname from first_name and last_name.
        
        Args:
            obj (User): The User instance to get the fullname for.
            
        Returns:
            str: The user's full name if available, otherwise the username.
        """
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username