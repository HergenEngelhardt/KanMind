from .registration_views import RegisterView
from .auth_serializers import CustomAuthTokenSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .auth_utils import AuthResponseMixin, GuestUserMixin
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


class LoginView(APIView):
    """
    API view for user login.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle POST request for user login.
        
        Args:
            request: HTTP request object containing login credentials
            
        Returns:
            Response: JSON response with user data and token or error message
        """
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            authenticated_user = authenticate(username=user.username, password=password)
            if authenticated_user:
                token, created = Token.objects.get_or_create(user=authenticated_user)
                return Response({
                    'token': token.key,
                    'user': {
                        'id': authenticated_user.id,
                        'email': authenticated_user.email,
                        'username': authenticated_user.username,
                        'first_name': authenticated_user.first_name,
                        'last_name': authenticated_user.last_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class EmailCheckView(APIView):
    """
    API view for checking if an email exists and retrieving user information.
    """
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        Handle GET request to check email existence and return user data.
        
        Args:
            request: HTTP request object containing email parameter
            
        Returns:
            Response: JSON response with user data or error message
        """
        email = request.GET.get('email')
        if not email:
            return Response({'error': 'Email parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            user_data = self._build_user_response(user)
            return Response(user_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def _build_user_response(self, user):
        """
        Build user response data dictionary.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            dict: Dictionary containing user information
        """
        fullname = self._get_user_fullname(user)
        return {
            'id': user.id,
            'email': user.email,
            'fullname': fullname,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    
    def _get_user_fullname(self, user):
        """
        Generate full name from user first and last name.
        
        Args:
            user (User): Django User model instance
            
        Returns:
            str: User's full name or fallback identifier
        """
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return user.email.split('@')[0] if user.email else user.username


class GuestLoginView(APIView, AuthResponseMixin, GuestUserMixin):
    """
    API view for guest user login.
    
    Provides endpoint for creating or retrieving guest users and their authentication tokens.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request for guest login.
        
        Creates or retrieves a guest user and generates an authentication token.
        
        Args:
            request: HTTP request object containing the login request data.
            
        Returns:
            Response: JSON response containing user data and authentication token
                     with HTTP 200 status code.
                     
        Raises:
            Exception: May raise exceptions from token generation or user creation.
        """
        guest_user = self._get_or_create_guest_user()
        token = self._get_or_create_token(guest_user)
        
        return Response(
            self._build_user_data(guest_user, token),
            status=status.HTTP_200_OK,
        )


# Function-based view wrappers
def login_view(request):
    """
    Function-based view wrapper for LoginView.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: Login view response
    """
    view = LoginView.as_view()
    return view(request)


def registration_view(request):
    """
    Function-based view wrapper for RegisterView.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: Registration view response
    """
    view = RegisterView.as_view()
    return view(request)


def email_check(request):
    """
    Function-based view wrapper for EmailCheckView.
    
    Args:
        request: HTTP request object
        
    Returns:
        Response: Email check view response
    """
    view = EmailCheckView.as_view()
    return view(request)


