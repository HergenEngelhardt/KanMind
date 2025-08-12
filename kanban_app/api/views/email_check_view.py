"""
View for checking if an email exists in the system.

This module contains the EmailCheckView for verifying if email addresses
are already registered in the system.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from kanban_app.api.serializers.user_serializers import UserSerializer

User = get_user_model()

class EmailCheckView(APIView):
    """
    View for checking if an email exists in the system.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Checks if the provided email address is registered.
        
        Args:
            request (Request): HTTP request with email query parameter
            
        Returns:
            Response: User data if found or 404 if not found
            
        Raises:
            Http404: If email is not found
        """
        email = request.query_params.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'Email not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )