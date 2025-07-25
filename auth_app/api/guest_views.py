from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .auth_utils import AuthResponseMixin, GuestUserMixin


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