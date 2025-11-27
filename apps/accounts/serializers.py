from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, PhoneVerification


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name', 
            'role', 'is_phone_verified', 'is_email_verified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'help_text': 'Primary email address for the user'},
            'phone': {'help_text': 'E.164 formatted phone number'},
            'role': {'help_text': "User role: 'candidate' or 'employer'"},
            'is_phone_verified': {'help_text': 'Whether the phone has been verified'},
            'is_email_verified': {'help_text': 'Whether the email has been verified'},
        }


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone', 'full_name', 
            'password', 'password_confirm', 'role'
        ]
        extra_kwargs = {
            'username': {'help_text': 'Unique username, used for login'},
            'email': {'help_text': 'Valid email address for login and communication'},
            'phone': {'help_text': 'Optional phone number, used for SMS verification'},
            'full_name': {'help_text': 'Display full name of the user'},
            'role': {'help_text': "Either 'candidate' or 'employer'"},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        
        # Validate role
        if attrs.get('role') not in ['candidate', 'employer']:
            raise serializers.ValidationError({"role": "Invalid role. Choose 'candidate' or 'employer'"})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    username = serializers.CharField(required=False, help_text='Username — one of username/email/phone is required')
    email = serializers.EmailField(required=False, help_text='Email — one of username/email/phone is required')
    phone = serializers.CharField(required=False, help_text='Phone — one of username/email/phone is required')
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        phone = attrs.get('phone')
        password = attrs.get('password')
        
        # At least one identifier must be provided
        if not any([username, email, phone]):
            raise serializers.ValidationError(
                "Must provide username, email, or phone"
            )
        
        # Try to find user
        user = None
        if username:
            user = User.objects.filter(username=username).first()
        elif email:
            user = User.objects.filter(email=email).first()
        elif phone:
            user = User.objects.filter(phone=phone).first()
        
        if user and user.check_password(password):
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError("Invalid credentials")


class PhoneVerificationSerializer(serializers.ModelSerializer):
    """Serializer for phone verification"""
    
    class Meta:
        model = PhoneVerification
        fields = ['phone', 'code']
        extra_kwargs = {
            'phone': {'help_text': 'Phone number to verify'},
            'code': {'help_text': '6-digit verification code sent via SMS'}
        }
    
    def validate_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Code must be 6 digits")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        help_text='Current password'
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='New password (must meet validation rules)'
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        help_text='Repeat new password for confirmation'
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "New passwords don't match"}
            )
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    