"""
Authentication views for the KanMind API.

This module contains views for user registration, login, and guest access.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .serializers import UserSerializer, RegistrationSerializer, LoginSerializer

User = get_user_model()


class RegistrationView(APIView):
    """
    View for user registration functionality.
    
    Handles new user creation with validation of required fields.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Create a new user account and generate an auth token.
        
        Args:
            request (Request): The HTTP request with user registration data.
            
        Returns:
            Response: User data with authentication token or validation errors.
            
        Raises:
            ValidationError: If provided data is invalid.
        """
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'fullname': user.get_full_name(),
                'email': user.email
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    View for user login functionality.
    
    Authenticates existing users and provides authentication token.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Authenticate a user and generate an auth token.
        
        Args:
            request (Request): The HTTP request with login credentials.
            
        Returns:
            Response: User data with authentication token or error message.
            
        Raises:
            ValidationError: If provided credentials are invalid.
        """
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.id,
                    'fullname': user.get_full_name(),
                    'email': user.email
                }, status=status.HTTP_200_OK)
            
            return Response({
                'detail': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GuestLoginView(APIView):
    """
    View for guest login functionality.
    
    Creates a temporary guest session or returns an existing guest account.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Create or retrieve a guest account and generate an auth token.
        
        Args:
            request (Request): The HTTP request.
            
        Returns:
            Response: User data with authentication token.
        """
        guest_email = "kevin@kovacsi.de"
        guest_password = "asdasdasd"
        
        try:
            user = User.objects.get(email=guest_email)
        except User.DoesNotExist:
            user = self._create_guest_user(guest_email, guest_password)
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'fullname': user.get_full_name(),
            'email': user.email
        }, status=status.HTTP_200_OK)
    
    def _create_guest_user(self, email, password):
        """
        Create a new guest user.
        
        Args:
            email (str): The email for the guest user.
            password (str): The password for the guest user.
            
        Returns:
            User: The created guest user.
        """
        return User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name="Guest",
            last_name="Guest"
        )