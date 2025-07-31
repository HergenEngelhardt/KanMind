"""
Serializers for user authentication operations.

This module contains serializers for user registration and login operations
with proper validation and data transformation.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data representation.
    
    Provides basic user information for API responses including
    name fields and email without sensitive data.
    """
    
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'fullname')
        read_only_fields = ('id',)
    
    def get_fullname(self, obj):
        """
        Get user's full name or fallback to username.
        
        Args:
            obj (User): User instance
            
        Returns:
            str: Full name or username if name fields empty
        """
        fullname = f"{obj.first_name} {obj.last_name}".strip()
        return fullname or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation.
    
    Handles user creation with encrypted password and proper validation
    of all required fields including email uniqueness.
    """
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
    
    def validate_email(self, value):
        """
        Validate email uniqueness.
        
        Args:
            value (str): Email address to validate
            
        Returns:
            str: Validated email address
            
        Raises:
            ValidationError: If email already exists
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value.lower().strip()
    
    def validate_username(self, value):
        """
        Validate username uniqueness.
        
        Args:
            value (str): Username to validate
            
        Returns:
            str: Validated username
            
        Raises:
            ValidationError: If username already exists
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value.strip()
    
    def create(self, validated_data):
        """
        Create user with encrypted password.
        
        Args:
            validated_data (dict): Validated user registration data
            
        Returns:
            User: Created user instance with encrypted password
            
        Raises:
            IntegrityError: If username or email already exists
        """
        return self._create_user_instance(validated_data)
    
    def _create_user_instance(self, data):
        """
        Create and return user instance.
        
        Args:
            data (dict): User creation data
            
        Returns:
            User: Created user instance
        """
        return User.objects.create_user(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password']
        )


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login credentials validation.
    
    Validates email and password format before authentication
    attempt to ensure proper data structure.
    """
    
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate_email(self, value):
        """
        Validate email format and presence.
        
        Args:
            value (str): Email address to validate
            
        Returns:
            str: Validated email address
            
        Raises:
            ValidationError: If email format is invalid
        """
        return value.lower().strip()
    
    def validate_password(self, value):
        """
        Validate password presence and basic requirements.
        
        Args:
            value (str): Password to validate
            
        Returns:
            str: Validated password
            
        Raises:
            ValidationError: If password is empty or too short
        """
        if len(value) < 3:
            raise serializers.ValidationError("Password too short")
        return value