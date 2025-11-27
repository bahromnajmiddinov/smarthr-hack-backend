from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
import random

from .models import User, PhoneVerification
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    LoginSerializer,
    PhoneVerificationSerializer,
    PasswordChangeSerializer
)
from .tasks import send_verification_sms
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


@extend_schema(
    summary="Register a new user",
    description="Create a new user account. Returns the created user and a pair of JWT tokens.",
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description="User + tokens object")},
    tags=["Accounts"]
)
class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Authenticate user and return tokens",
    description="Authenticate with username/email/phone and password. Returns the user and JWT tokens.",
    request=LoginSerializer,
    responses={200: OpenApiResponse(description='User + tokens')},
    tags=["Accounts"]
)
class LoginView(APIView):
    """User login endpoint"""
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


@extend_schema(
    summary="Logout (revoke refresh token)",
    description="Blacklist the provided refresh token so it can no longer be used to refresh access tokens.",
    request=None,
    responses={200: OpenApiResponse(description='Success message')},
    tags=["Accounts"]
)
class LogoutView(APIView):
    """User logout endpoint"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Retrieve or update current user's profile",
    description="Retrieve the current authenticated user's profile or update it.",
    request=UserSerializer,
    responses={200: UserSerializer},
    tags=["Accounts"]
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """Current user profile view"""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@extend_schema(
    summary="Send phone verification code",
    description="Send a 6-digit verification code to the user's phone number. Returns expiry info.",
    request=OpenApiResponse(description='phone string can be supplied to override user phone'),
    responses={200: OpenApiResponse(description='Verification message')},
    tags=["Accounts"]
)
class SendPhoneVerificationView(APIView):
    """Send verification code to phone"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        phone = request.data.get('phone', user.phone)
        
        if not phone:
            return Response(
                {'error': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate 6-digit code
        code = str(random.randint(100000, 999999))
        
        # Create verification record
        verification = PhoneVerification.objects.create(
            user=user,
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send SMS asynchronously
        send_verification_sms.delay(phone, code)
        
        return Response({
            'message': 'Verification code sent',
            'expires_in_minutes': 10
        })


@extend_schema(
    summary="Verify phone number using code",
    description="Validates the 6-digit code sent to the user's phone and marks the phone as verified.",
    request=PhoneVerificationSerializer,
    responses={200: OpenApiResponse(description='Success message'), 400: OpenApiResponse(description='Validation errors')},
    tags=["Accounts"]
)
class VerifyPhoneView(APIView):
    """Verify phone with code"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        
        try:
            verification = PhoneVerification.objects.get(
                user=request.user,
                phone=phone,
                code=code,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
            
            verification.is_verified = True
            verification.save()
            
            # Update user
            request.user.phone = phone
            request.user.is_phone_verified = True
            request.user.save()
            
            return Response({
                'message': 'Phone verified successfully'
            })
            
        except PhoneVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired verification code'},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    summary="Change the current user's password",
    description="Change password by providing old_password and a new password with confirmation.",
    request=PasswordChangeSerializer,
    responses={200: OpenApiResponse(description='Success message')},
    tags=["Accounts"]
)
class PasswordChangeView(APIView):
    """Change user password"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Change password
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        })
        