"""
Authentication serializers for KanMind API.

This module contains serializers for user authentication, registration, and login.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Used for representing user data in responses.
    """
    fullname = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']
        read_only_fields = ['id']
    
    def get_fullname(self, obj):
        """
        Get the full name of the user.
        
        Args:
            obj (User): The user instance.
            
        Returns:
            str: The user's full name.
        """
        return obj.get_full_name()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles validation and creation of new user accounts.
    """
    fullname = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    repeated_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'fullname', 'password', 'repeated_password']
    
    def validate_email(self, value):
        """
        Check if a user with this email already exists.
        
        Args:
            value (str): The email to validate
            
        Returns:
            str: The validated email
            
        Raises:
            ValidationError: If a user with this email already exists
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return value
    
    def validate(self, data):
        """
        Validate user registration data.
        
        Args:
            data (dict): The data to validate.
            
        Returns:
            dict: The validated data.
            
        Raises:
            ValidationError: If passwords don't match.
        """
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({"repeated_password": "Passwords don't match"})
        
        validate_password(data['password'])
        
        return data
    
    def create(self, validated_data):
        """
        Create a new user with the validated data.
        
        Args:
            validated_data (dict): The validated user data.
            
        Returns:
            User: The created user instance.
        """
        fullname = validated_data.pop('fullname')
        validated_data.pop('repeated_password')
        
        name_parts = fullname.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['email'],
            first_name=first_name,
            last_name=last_name,
            **validated_data
        )
        
        user.set_password(password)
        user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Validates login credentials.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )