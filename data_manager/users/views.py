import logging
from django.contrib.auth import authenticate, logout, get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from rest_framework.authentication import TokenAuthentication
from .serializers import UserSerializer, LoginSerializer, InviteUserSerializer
from .permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from accounts.models import Account, AccountMember
from .models import Role

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=UserSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer, description="User registered"),
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def post(self, request):
        logger.info(f"Registration attempt with data: {request.data}")
        serializer = UserSerializer(data=request.data, context={'request': request})
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
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful", examples=[
                OpenApiExample("Success", value={"token": "some-token"})
            ]),
            401: OpenApiResponse(description="Invalid credentials")
        }
    )
    def post(self, request):
        logger.info(f"Login attempt for email: {request.data.get('email')}")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                request=request,
                username=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                logger.info(f"User {user.email} logged in successfully")
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            logger.warning("Invalid login credentials")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        logger.warning(f"Invalid login data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Logout successful", examples=[
                OpenApiExample("Success", value={"message": "Logged out successfully"})
            ]),
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
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        request=InviteUserSerializer,
        responses={
            201: OpenApiResponse(description="User invited"),
            400: OpenApiResponse(description="Invalid data")
        }
    )
    def post(self, request):
        logger.info(f"Invite attempt by {request.user.email} for: {request.data.get('email')}")
        serializer = InviteUserSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            account_id = serializer.validated_data['account_id']
            if not Account.objects.filter(id=account_id, members__user=request.user, members__role__role_name='Admin').exists():
                return Response({"error": "Invalid or unauthorized account"}, status=status.HTTP_403_FORBIDDEN)
            user = User.objects.filter(email=email).first()
            if user:
                logger.info(f"Existing user {email} found")
                AccountMember.objects.get_or_create(
                    account_id=account_id,
                    user=user,
                    defaults={'role': Role.objects.get(role_name='Normal user'), 'created_by': request.user, 'updated_by': request.user}
                )
                return Response({"message": "User added to account!"}, status=status.HTTP_200_OK)
            import secrets
            new_user = User.objects.create_user(
                email=email,
                password=secrets.token_hex(16),
                created_by=request.user,
                updated_by=request.user
            )
            AccountMember.objects.create(
                account=Account.objects.get(id=account_id),
                user=new_user,
                role=Role.objects.get(role_name='Normal user'),
                created_by=request.user,
                updated_by=request.user
            )
            logger.info(f"New user {email} invited and added to account")
            return Response({"message": "User invited and added to account!"}, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid invite data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        responses={200: UserSerializer(many=True)},
        parameters=[{'name': 'email', 'type': 'string', 'in': 'query', 'description': 'Filter by email'}]
    )
    def get(self, request, *args, **kwargs):
        is_admin = IsAdminUser().has_permission(request, self)
        if not is_admin:
            queryset = User.objects.filter(id=request.user.id)
        else:
            queryset = User.objects.all()
            email_filter = request.query_params.get('email')
            if email_filter:
                queryset = queryset.filter(email__icontains=email_filter)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserUpdateView(generics.UpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    lookup_field = 'id'

    def get_queryset(self):
        is_admin = IsAdminUser().has_permission(self.request, self)
        if is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @extend_schema(
        request=UserSerializer,
        responses={200: UserSerializer, 403: "Permission denied", 404: "Not found"}
    )
    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)