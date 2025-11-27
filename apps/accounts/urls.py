from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    SendPhoneVerificationView,
    VerifyPhoneView,
    PasswordChangeView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    
    # Phone verification
    path('phone/send-code/', SendPhoneVerificationView.as_view(), name='send_phone_code'),
    path('phone/verify/', VerifyPhoneView.as_view(), name='verify_phone'),
]
