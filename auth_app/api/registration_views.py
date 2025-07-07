from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from .auth_utils import AuthResponseMixin


class RegisterView(APIView, AuthResponseMixin):
    """User registration endpoint."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            return self._create_user_response(serializer)
        return self._validation_error_response(serializer)

    def _create_user_response(self, serializer):
        user = serializer.save()
        token = self._get_or_create_token(user)
        
        return Response(
            self._build_user_data(user, token),
            status=status.HTTP_201_CREATED,
        )

    def _validation_error_response(self, serializer):
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )