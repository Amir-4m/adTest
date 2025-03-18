from typing import Optional, Type

from django.contrib.auth import get_user_model, password_validation
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer, PasswordField
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from apps.users.models import User

from ..models import UserVerificationRequest
from ..services import AuthenticationService
from ..tasks import send_account_verification_email, send_forget_password_email


class LifeTimeTokenSerializer:

    def validate(self, attrs):
        # adding lifetime to data
        email = attrs.get('email', '').lower()
        attrs['email'] = email
        data = super().validate(attrs)
        data['lifetime'] = int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
        if email:
            qs = UserVerificationRequest.objects.filter(email=email)
            if not qs.exists():
                raise ValidationError("verification does not exists, use resend verification.")
            if qs.exists() and qs.filter(used=True, is_active=False).order_by('-created_at').exists() is False:
                raise PermissionDenied({'verified': False})
        return data


class LifeTimeTokenObtainSerializer(LifeTimeTokenSerializer):
    def validate(self, attrs):
        data = super(LifeTimeTokenObtainSerializer, self).validate(attrs)
        return data


class LifeTimeTokenRefreshSerializer(LifeTimeTokenSerializer, TokenRefreshSerializer):
    pass


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    phone_number = serializers.RegexField(regex=r'^\+?1?\d{10,15}$')
    password = serializers.CharField(max_length=100, write_only=True)
    confirm_password = serializers.CharField(max_length=100, write_only=True)
    gender = serializers.ChoiceField(choices=User.GenderChoices.choices)

    def validate_password(self, value):
        if value != self.initial_data['confirm_password']:
            raise ValidationError(_('entered passwords are not the same.'))
        password_validation.validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email__icontains=value.lower(), is_temp=False).exists():
            raise ValidationError(
                _('This email address is already registered. You can only create one profile per email address.'))
        return value

    def create(self, validated_data):
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        email = validated_data['email'].lower()
        password = validated_data['password']
        gender = validated_data['gender']
        phone_number = validated_data['phone_number']
        username = email
        if User.objects.filter(email=email, is_temp=True, is_active=True).exists():
            user = User.objects.filter(email=email, is_temp=True, is_active=True).first()
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.gender = gender
            user.phone_number = phone_number
            user.save()
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                phone_number=phone_number,
                is_active=True

            )
        UserVerificationRequest.objects.create(
            user=user,
            email=email,
            used=False,
            is_active=True
        )
        send_account_verification_email.delay(user.id)
        return user

    def update(self, instance, validated_data):
        pass


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    class Meta:
        model = User
        fields = ('old_password', 'password', 'confirm_password')

    def validate_old_password(self, old_password):
        if not self.instance.check_password(old_password):
            raise serializers.ValidationError(_('Current Password is incorrect'))
        return old_password

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('entered passwords are not the same.')
        password_validation.validate_password(attrs['password'])
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance


class ChangeEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('email',)

    def validate_email(self, email):
        if User.objects.filter(email__icontains=email.lower()).exists():
            raise serializers.ValidationError(_('this email has been taken already!'))
        return email

    def update(self, instance, validated_data):
        send_account_verification_email.delay(instance.id)
        return instance


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        value = value.lower()
        if not User.objects.filter(email__icontains=value).exists():
            raise ValidationError(_('user with this email does not exists.'))
        if not AuthenticationService.is_verified(value):
            raise ValidationError(_('Please finish your Email verification before resetting your password.'))
        return value

    def create(self, validated_data):
        email = validated_data['email'].lower()
        user = get_user_model().objects.filter(email__icontains=email).first()
        send_forget_password_email.delay(user.id)
        return {'forget_password_request': 'created'}


class ForgetPasswordConfirmSerializer(serializers.Serializer):
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    class Meta:
        model = User
        fields = ('password', 'confirm_password')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('entered passwords are not the same.')
        password_validation.validate_password(attrs['password'])
        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        value = value.lower()
        if not User.objects.filter(email__icontains=value).exists():
            raise ValidationError(_('user with this email does not exists.'))
        if AuthenticationService.is_verified(value):
            raise ValidationError(_('user with this email has been verified already.'))
        return value

    def create(self, validated_data):
        email = validated_data['email'].lower()
        user = get_user_model().objects.filter(email__icontains=email).first()
        send_account_verification_email.delay(user.id)
        return user


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    device_token = serializers.CharField(allow_null=True, allow_blank=True, required=False)

    def validate_refresh(self, value):
        try:
            RefreshToken(value)
        except Exception:
            raise serializers.ValidationError("Invalid refresh token")
        return value
