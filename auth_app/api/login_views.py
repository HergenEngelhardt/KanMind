from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from .auth_serializers import CustomAuthTokenSerializer
from .auth_utils import AuthResponseMixin


class LoginView(ObtainAuthToken, AuthResponseMixin):
    """User login endpoint."""
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self._get_validated_serializer(request)
            user = serializer.validated_data["user"]
            token = self._get_or_create_token(user)
            
            return Response(self._build_user_data(user, token))
            
        except ValidationError as e:
            return Response(
                {"error": "Invalid credentials provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Login failed due to server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_validated_serializer(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return serializer