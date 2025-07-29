from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging

from .serializers import RegisterSerializer, UserLoginSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def registration_view(request):
    """
    Register a new user account and return authentication token.
    
    Args:
        request: HTTP request containing user registration data
        
    Returns:
        Response: User data with authentication token or validation errors
    """
    logger.info(f"Registration request from IP: {request.META.get('REMOTE_ADDR')}")
    logger.info(f"Registration data: {request.data}")
    
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            logger.info(f"User registered successfully: {user.email}")
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            }, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            logger.error(f"Registration failed - IntegrityError: {str(e)}")
            return Response({
                'error': 'A user with this email or username already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        logger.error(f"Registration validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return authentication token.
    
    Args:
        request: HTTP request containing login credentials
        
    Returns:
        Response: Authentication token and user data or error message
    """
    logger.info(f"Login request from IP: {request.META.get('REMOTE_ADDR')}")
    
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(email=email)
            authenticated_user = authenticate(username=user.username, password=password)
            
            if authenticated_user:
                token, created = Token.objects.get_or_create(user=authenticated_user)
                logger.info(f"Successful login for user: {email}")
                
                return Response({
                    'token': token.key,
                    'user': {
                        'id': authenticated_user.id,
                        'email': authenticated_user.email,
                        'username': authenticated_user.username,
                        'first_name': authenticated_user.first_name,
                        'last_name': authenticated_user.last_name,
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Failed login attempt for user: {email}")
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            logger.warning(f"Login attempt for non-existent user: {email}")
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        logger.error(f"Login validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def email_check(request):
    """
    Check if user exists by email and return user information.
    
    Args:
        request: HTTP request with email parameter
        
    Returns:
        Response: User information or error message
    """
    email = request.GET.get('email')
    if not email:
        return Response(
            {'error': 'Email parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        return Response({
            'id': user.id,
            'email': user.email,
            'fullname': f"{user.first_name} {user.last_name}".strip() or user.username
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )