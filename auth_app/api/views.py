"""
Authentication views for the API.

Provides views for user registration, login and email verification.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, LoginSerializer
import logging

logger = logging.getLogger(__name__)


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
        
        logger.info(f"User registered successfully: {user.username}")
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
            'user_id': user.id,
            'email': user.email
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
        """
        serializer = LoginSerializer(data=request.data)
        
        if not self._is_valid_login(serializer):
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return self._authenticate_and_respond(serializer)
    
    def _is_valid_login(self, serializer):
        """
        Validate login data.
        
        Args:
            serializer (LoginSerializer): The serializer to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        return serializer.is_valid()
    
    def _authenticate_and_respond(self, serializer):
        """
        Authenticate user and generate response.
        
        Args:
            serializer (LoginSerializer): Validated serializer
            
        Returns:
            Response: Success or error response
        """
        user = self._authenticate_user(serializer.validated_data)
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
                
        token_data = self._create_token_response(user)
        
        logger.info(f"User logged in successfully: {user.username}")
        return Response(token_data, status=status.HTTP_200_OK)
    
    def _authenticate_user(self, credentials):
        """
        Authenticate user with credentials.
        
        Args:
            credentials (dict): Username and password
            
        Returns:
            User: Authenticated user or None
        """
        return authenticate(
            username=credentials['username'],
            password=credentials['password']
        )
    
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
        
        if not self._validate_email_param(email):
            return Response(
                {'error': 'Email parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return self._check_email_existence(email)
    
    def _validate_email_param(self, email):
        """
        Validate that email parameter exists.
        
        Args:
            email (str): Email parameter from request
            
        Returns:
            bool: True if email exists, False otherwise
        """
        return email is not None
    
    def _check_email_existence(self, email):
        """
        Check if email exists and format response.
        
        Args:
            email (str): Email to check
            
        Returns:
            Response: Email existence information
        """
        try:
            user = User.objects.get(email=email)
            return Response(self._format_user_data(user))
        except User.DoesNotExist:
            return Response({'exists': False})
    
    def _format_user_data(self, user):
        """
        Format user data for response.
        
        Args:
            user (User): User object to format
            
        Returns:
            dict: Formatted user data
        """
        return {
            'exists': True,
            'user_id': user.id,
            'username': user.username
        }


# Function-based view implementations with decorators
@api_view(['POST'])
@permission_classes([AllowAny])
def registration_view(request):
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
    
    if not _validate_registration_data(serializer):
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    return _process_registration(serializer)


def _validate_registration_data(serializer):
    """
    Validate registration serializer data.
    
    Args:
        serializer (RegisterSerializer): Serializer to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return serializer.is_valid()


def _process_registration(serializer):
    """
    Process valid registration data.
    
    Args:
        serializer (RegisterSerializer): Validated serializer
        
    Returns:
        Response: Created response with user data
    """
    user = serializer.save()
    token_data = create_token_response(user)
    
    logger.info(f"User registered successfully: {user.username}")
    return Response(token_data, status=status.HTTP_201_CREATED)


def create_token_response(user):
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


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Handle user login request.
    
    Args:
        request (Request): HTTP request with login credentials
        
    Returns:
        Response: User data with token or error message
        
    Raises:
        ValidationError: If login data is invalid
    """
    serializer = LoginSerializer(data=request.data)
    
    if not _validate_login_data(serializer):
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return _process_login(serializer)


def _validate_login_data(serializer):
    """
    Validate login serializer data.
    
    Args:
        serializer (LoginSerializer): Serializer to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return serializer.is_valid()


def _process_login(serializer):
    """
    Process valid login data.
    
    Args:
        serializer (LoginSerializer): Validated serializer
        
    Returns:
        Response: Success or error response
    """
    user = authenticate_user(serializer.validated_data)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
            
    token_data = create_token_response(user)
    
    logger.info(f"User logged in successfully: {user.username}")
    return Response(token_data, status=status.HTTP_200_OK)


def authenticate_user(credentials):
    """
    Authenticate user with credentials.
    
    Args:
        credentials (dict): Username and password
        
    Returns:
        User: Authenticated user or None
    """
    return authenticate(
        username=credentials['username'],
        password=credentials['password']
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def email_check_view(request):
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
    
    if not _validate_email_parameter(email):
        return Response(
            {'error': 'Email parameter is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return _check_email_exists(email)


def _validate_email_parameter(email):
    """
    Validate email parameter exists.
    
    Args:
        email (str): Email parameter to validate
        
    Returns:
        bool: True if email parameter exists
    """
    return email is not None


def _check_email_exists(email):
    """
    Check if email exists in database.
    
    Args:
        email (str): Email to check
        
    Returns:
        Response: Email existence information
    """
    try:
        user = User.objects.get(email=email)
        return Response(format_user_data(user))
    except User.DoesNotExist:
        return Response({'exists': False})


def format_user_data(user):
    """
    Format user data for response.
    
    Args:
        user (User): User object to format
        
    Returns:
        dict: Formatted user data
    """
    return {
        'exists': True,
        'user_id': user.id,
        'username': user.username
    }