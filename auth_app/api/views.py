from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer
import logging

logger = logging.getLogger(__name__)


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")
        password = attrs.get("password")

        if email == "kevin@kovacsi.de" and password == "asdasdasd":
            try:
                guest_user = User.objects.get(username="guest@example.com")
            except User.DoesNotExist:
                guest_user = User.objects.create_user(
                    username="guest@example.com",
                    email="guest@example.com",
                    password="guest1234",
                    first_name="Guest",
                    last_name="User",
                )
            attrs["user"] = guest_user
            return attrs

        if (not username and not email) or not password:
            msg = "Entweder E-Mail oder Benutzername sowie Passwort müssen angegeben werden."
            raise serializers.ValidationError(msg, code="authorization")

        if email and not username:
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                msg = "Benutzer mit dieser E-Mail-Adresse existiert nicht."
                raise serializers.ValidationError(msg, code="authorization")

        user = authenticate(username=username, password=password)
        if not user:
            msg = "Anmeldung mit den angegebenen Anmeldedaten nicht möglich."
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user_id": user.pk,
                    "email": user.email,
                    "fullname": f"{user.first_name} {user.last_name}",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        print("Received login data:", request.data)

        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "email": user.email,
                "fullname": f"{user.first_name} {user.last_name}",
            }
        )


class GuestLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug("Guest login requested")
        try:
            guest_user = User.objects.get(username="guest@example.com")
            logger.debug("Found existing guest user")
        except User.DoesNotExist:
            logger.debug("Creating new guest user")
            guest_user = User.objects.create_user(
                username="guest@example.com",
                email="guest@example.com",
                password="guest1234",
                first_name="Guest",
                last_name="User",
            )

        token, created = Token.objects.get_or_create(user=guest_user)
        logger.debug(f"Generated token: {token.key}")

        response_data = {
            "token": token.key,
            "user_id": guest_user.pk,
            "email": guest_user.email,
            "fullname": f"{guest_user.first_name} {guest_user.last_name}",
        }

        return Response(response_data)
