from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User


class EmailCheckView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')
        
        if not email:
            return Response(
                {"error": "Email parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            return self._user_found_response(user)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

    def _user_found_response(self, user):
        first_name = (user.first_name or "").strip()
        last_name = (user.last_name or "").strip()
        
        if first_name and last_name:
            fullname = f"{first_name} {last_name}"
        elif first_name:
            fullname = first_name
        elif last_name:
            fullname = last_name
        else:
            fullname = user.email.split('@')[0] if user.email else user.username
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "fullname": fullname,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        
        return Response(user_data, status=status.HTTP_200_OK)