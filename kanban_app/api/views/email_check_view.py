"""
Email check view for the KanMind API.

This module contains the view for checking if an email is already registered.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from auth_app.api.serializers import UserSerializer

User = get_user_model()


class EmailCheckView(APIView):
    """
    View for checking if an email is already registered.
    
    Requires authentication to prevent user enumeration attacks.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Check if an email address is already associated with a user.
        
        Args:
            request (Request): The HTTP request with email query parameter.
            
        Returns:
            Response: User data if found, 404 if not found.
            
        Raises:
            Http404: If the email does not exist.
            ValidationError: If email is missing or invalid.
        """
        email = self._get_email_from_request(request)
        
        if not email:
            return Response(
                {"detail": "Email parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"detail": "User with this email does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_email_from_request(self, request):
        """
        Extract email from request query parameters.
        
        Args:
            request (Request): The HTTP request.
            
        Returns:
            str: The email address or None if not provided.
        """
        return request.query_params.get('email')