"""
Serializers for authentication endpoints.

Provides serializers for user registration and login.
"""
from rest_framework import serializers
from django.contrib.auth.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles validation and creation of new user accounts.
    """
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 
                  'first_name', 'last_name')
    
    def validate(self, data):
        """
        Validate registration data.
        
        Args:
            data (dict): Registration data to validate
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: If passwords don't match or email/username exist
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords don't match"}
            )
        
        self._validate_username_email(data)
            
        return data
    
    def _validate_username_email(self, data):
        """
        Validate username and email uniqueness.
        
        Args:
            data (dict): Data containing username and email
            
        Raises:
            ValidationError: If username or email already exists
        """
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError(
                {"username": "Username already exists"}
            )
            
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "Email already exists"}
            )
    
    def create(self, validated_data):
        """
        Create a new user.
        
        Args:
            validated_data (dict): Validated registration data
            
        Returns:
            User: Created user object
        """
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Validates login credentials.
    """
    username = serializers.CharField()
    password = serializers.CharField()