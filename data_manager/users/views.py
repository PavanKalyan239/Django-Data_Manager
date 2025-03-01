# users/views.py
import logging
from django.contrib.auth import authenticate, logout, get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from .serializers import UserSerializer, LoginSerializer, InviteUserSerializer
from .permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterView(APIView):
    """
    Register a new user without authentication.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=UserSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User registered successfully",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "message": "User registered successfully!",
                            "user": {"id": 1, "email": "test@example.com", "role": "user"},
                            "token": "some-token-string"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def post(self, request):
        logger.info(f"Registration attempt with data: {request.data}")
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                token = Token.objects.get(user=user)
                logger.info(f"User {user.email} registered successfully")
                return Response({
                    "message": "User registered successfully!",
                    "user": serializer.data,
                    "token": token.key
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Registration failed: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        logger.warning(f"Invalid registration data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    Log in a user with a valid token (re-authentication).
    Requires Token Authentication.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"token": "some-token-string", "role": "user"}
                    )
                ]
            ),
            401: OpenApiResponse(description="Invalid credentials or unauthorized")
        }
    )
    def post(self, request):
        logger.info(f"Login attempt for email: {request.data.get('email')}")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                logger.info(f"User {user.email} logged in successfully")
                return Response({
                    "token": token.key,
                    "role": user.role
                }, status=status.HTTP_200_OK)
            logger.warning("Invalid login credentials")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        logger.warning(f"Invalid login data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    """
    Log out an authenticated user.
    Requires Token Authentication.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Logout successful",
                examples=[OpenApiExample("Success", value={"message": "Logged out successfully"})]
            ),
            400: OpenApiResponse(description="Logout failed")
        }
    )
    def post(self, request):
        try:
            logger.info(f"Logout attempt for user: {request.user.email}")
            request.user.auth_token.delete()
            logout(request)
            logger.info("Logout successful")
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class InviteUserView(APIView):
    """
    Invite a user (admin only).
    Requires Token Authentication and admin role.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        request=InviteUserSerializer,
        responses={
            200: OpenApiResponse(
                description="User already exists",
                examples=[OpenApiExample("Exists", value={"message": "User already exists in the system!"})]
            ),
            201: OpenApiResponse(
                description="Invitation logged",
                examples=[OpenApiExample("Invited", value={"message": "User invited successfully (no email sent)!"})]
            ),
            403: OpenApiResponse(description="Permission denied (non-admin)")
        }
    )
    def post(self, request):
        logger.info(f"Invite attempt by {request.user.email} for: {request.data.get('email')}")
        serializer = InviteUserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.filter(email=email).first()
            if user:
                logger.info(f"Existing user {email} found")
                return Response({"message": "User already exists in the system!"}, 
                              status=status.HTTP_200_OK)
            logger.info(f"New user {email} invited (no email sent)")
            return Response({"message": "User invited successfully (no email sent)!"}, 
                          status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid invite data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)