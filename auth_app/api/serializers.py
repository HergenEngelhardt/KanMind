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
        fields = ['id', 'email', 'first_name', 'last_name', 'fullname']
        read_only_fields = ['id', 'email']
    
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
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']
    
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
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match"})
        
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
        validated_data.pop('password_confirm')
        
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['email'],
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