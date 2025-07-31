"""
Authentication views for user registration, login and email validation.

This module provides API endpoints for user authentication operations
including registration, login, and email existence checking.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging

from .serializers import RegisterSerializer, UserLoginSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def registration_view(request):
    """
    Handle user registration with validation and token creation.
    
    Args:
        request (Request): HTTP request with registration data
        
    Returns:
        Response: User data with authentication token or error details
        
    Raises:
        ValidationError: If registration data is invalid
        IntegrityError: If user already exists
    """
    return _process_registration(request.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Handle user login authentication with credential validation.
    
    Args:
        request (Request): HTTP request with login credentials
        
    Returns:
        Response: User data with authentication token or error details
        
    Raises:
        ValidationError: If credentials format is invalid
        AuthenticationError: If credentials are incorrect
    """
    return _process_login(request.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def email_check(request):
    """
    Check if user exists by email address.
    
    Args:
        request (Request): HTTP request with email query parameter
        
    Returns:
        Response: User data if found or error message
        
    Raises:
        ValidationError: If email parameter is missing
        DoesNotExist: If user with email not found
    """
    return _check_email_existence(request.query_params.get('email'))


def _process_registration(data):
    """
    Process user registration with validation.
    
    Args:
        data (dict): Registration form data
        
    Returns:
        Response: Success response with token or validation errors
    """
    serializer = RegisterSerializer(data=data)
    if not serializer.is_valid():
        return _validation_error(serializer.errors)
    
    try:
        user = serializer.save()
        return _create_auth_response(user, status.HTTP_201_CREATED)
    except IntegrityError:
        return _user_exists_error()


def _process_login(data):
    """
    Process user login with credential validation.
    
    Args:
        data (dict): Login credentials data
        
    Returns:
        Response: Success response with token or authentication error
    """
    serializer = UserLoginSerializer(data=data)
    if not serializer.is_valid():
        return _validation_error(serializer.errors)
    
    return _authenticate_user(
        serializer.validated_data['email'],
        serializer.validated_data['password']
    )


def _authenticate_user(email, password):
    """
    Authenticate user with email and password.
    
    Args:
        email (str): User email address
        password (str): User password
        
    Returns:
        Response: Authentication response with token or error
    """
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            logger.info(f"Successful login for user: {email}")
            return _create_auth_response(user, status.HTTP_200_OK)
        return _invalid_credentials_error()
    except User.DoesNotExist:
        return _invalid_credentials_error()


def _check_email_existence(email):
    """
    Check if user with given email exists.
    
    Args:
        email (str): Email address to check
        
    Returns:
        Response: User data if found or error response
    """
    if not email:
        return Response(
            {"error": "Email parameter is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        return _user_found_response(user)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


def _create_auth_response(user, response_status):
    """
    Create authentication response with user data and token.
    
    Args:
        user (User): Authenticated user instance
        response_status (int): HTTP status code for response
        
    Returns:
        Response: JSON response with user data and authentication token
    """
    token, created = Token.objects.get_or_create(user=user)
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'token': token.key
    }, status=response_status)


def _user_exists_error():
    """
    Create error response for existing user registration attempt.
    
    Returns:
        Response: HTTP 400 response with user exists error message
    """
    return Response({
        'error': 'A user with this email or username already exists.'
    }, status=status.HTTP_400_BAD_REQUEST)


def _invalid_credentials_error():
    """
    Create error response for invalid login credentials.
    
    Returns:
        Response: HTTP 401 response with invalid credentials error
    """
    return Response({
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)


def _validation_error(errors):
    """
    Create error response for validation failures.
    
    Args:
        errors (dict): Serializer validation error details
        
    Returns:
        Response: HTTP 400 response with validation error details
    """
    logger.error(f"Validation failed: {errors}")
    return Response(errors, status=status.HTTP_400_BAD_REQUEST)


def _user_found_response(user):
    """
    Create success response with user information.
    
    Args:
        user (User): User instance to return data for
        
    Returns:
        Response: HTTP 200 response with user data
    """
    fullname = f"{user.first_name} {user.last_name}".strip()
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'fullname': fullname or user.username
    }, status=status.HTTP_200_OK)