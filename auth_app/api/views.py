"""
Views for user authentication including registration, login, and guest access.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view, permission_classes
from .serializers import RegistrationSerializer
import logging

logger = logging.getLogger(__name__)

class RegistrationView(APIView):
    """
    View for registering new users.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Creates a new user and returns token with user info.
        
        Args:
            request: HTTP request object with registration data
            
        Returns:
            Response: JSON with token and user data or errors
        """
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return self._create_success_response(user, token)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_success_response(self, user, token):
        """
        Creates success response with user data and token.
        
        Args:
            user: User object
            token: Auth token
            
        Returns:
            Response: Success response with status 201
        """
        return Response({
            'token': token.key,
            'fullname': f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    View for user authentication and token generation.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Authenticates a user and returns token with user info.
        
        Args:
            request: HTTP request with login credentials
            
        Returns:
            Response: JSON with token and user data or errors
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not self._validate_credentials(email, password):
            return Response(
                {'error': 'Please provide both email and password'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self._authenticate_user(email, password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token, _ = Token.objects.get_or_create(user=user)
        return self._create_success_response(user, token)
    
    def _validate_credentials(self, email, password):
        """
        Validates that both email and password are provided.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            bool: True if both are provided
        """
        return email is not None and password is not None
    
    def _authenticate_user(self, email, password):
        """
        Authenticates user with provided credentials.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User: Authenticated user or None
        """
        return authenticate(username=email, email=email, password=password)
    
    def _create_success_response(self, user, token):
        """
        Creates success response with user data and token.
        
        Args:
            user: User object
            token: Auth token
            
        Returns:
            Response: Success response with status 200
        """
        return Response({
            'token': token.key,
            'fullname': f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'user_id': user.id
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_login_view(request):
    """
    Authenticate with pre-defined guest credentials.
    
    Args:
        request (Request): HTTP request
        
    Returns:
        Response: Authentication token and guest user information
        
    Raises:
        AuthenticationFailed: If guest account is unavailable
    """
    # Fest definierte Gastanmeldedaten
    email = "kevin@kovacsi.de"
    password = "asdasdasd"
    
    user = authenticate(username=email, email=email, password=password)
    
    if not user:
        # Überprüfen, ob der Gastbenutzer existiert
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            return Response(
                {'error': 'Guest account exists but password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Guest account not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    token, _ = Token.objects.get_or_create(user=user)
    
    return Response({
        'token': token.key,
        'fullname': f"{user.first_name} {user.last_name}".strip(),
        'email': user.email,
        'user_id': user.id
    }, status=status.HTTP_200_OK)