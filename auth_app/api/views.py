"""
Authentication views for the API.

Provides views for user registration, login and email verification.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from .serializers import RegisterSerializer, LoginSerializer
import logging

class RegistrationView(APIView):
    """
    View for user registration.
    
    Handles user signup and returns authentication token.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle user registration request.
        
        Args:
            request (Request): HTTP request with registration data
            
        Returns:
            Response: User data with token or validation errors
            
        Raises:
            ValidationError: If registration data is invalid
        """
        serializer = RegisterSerializer(data=request.data)
        
        if not self._is_valid_registration(serializer):
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return self._create_user_and_respond(serializer)
    
    def _is_valid_registration(self, serializer):
        """
        Validate registration data.
        
        Args:
            serializer (RegisterSerializer): The serializer to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return serializer.is_valid()
    
    def _create_user_and_respond(self, serializer):
        """
        Create user and generate response.
        
        Args:
            serializer (RegisterSerializer): Validated serializer
            
        Returns:
            Response: Created response with user data
        """
        user = serializer.save()
        token_data = self._create_token_response(user)
        
        return Response(token_data, status=status.HTTP_201_CREATED)
    
    def _create_token_response(self, user):
        """
        Create authentication token and response data.
        
        Args:
            user (User): User object to create token for
            
        Returns:
            dict: Token and user data for response
        """
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'user_id': user.id
        }


class LoginView(APIView):
    """
    View for user login.
    
    Authenticates user credentials and returns token.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle user login request.
        
        Args:
            request (Request): HTTP request with login credentials
            
        Returns:
            Response: User data with token or error message
            
        Raises:
            ValidationError: If login data is invalid
            AuthenticationFailed: If credentials are invalid
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"detail": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = self._get_user_by_email(email)
        
        if not user or not user.check_password(password):
            raise AuthenticationFailed("Invalid credentials")
            
        token_data = self._create_token_response(user)
        
        return Response(token_data, status=status.HTTP_200_OK)
    
    def _get_user_by_email(self, email):
        """
        Get user by email.
        
        Args:
            email (str): Email to search for
            
        Returns:
            User: User object if found, None otherwise
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def _create_token_response(self, user):
        """
        Create authentication token and response data.
        
        Args:
            user (User): User object to create token for
            
        Returns:
            dict: Token and user data for response
        """
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'user_id': user.id,
            'email': user.email
        }


class EmailCheckView(APIView):
    """
    View to check if email exists.
    
    Provides endpoint to verify email availability.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Check if email exists in the system.
        
        Args:
            request (Request): HTTP request with email parameter
            
        Returns:
            Response: User data or not found message
            
        Raises:
            ValidationError: If email parameter is missing
        """
        email = request.query_params.get('email')
        
        if not email:
            raise ValidationError({'email': 'Email parameter is required'})
        
        exists = User.objects.filter(email=email).exists()
        
        return Response({'exists': exists}, status=status.HTTP_200_OK)