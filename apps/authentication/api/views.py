from django.http import Http404
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.models import User

from .serializers import (
    RegisterSerializer, LifeTimeTokenObtainSerializer, LifeTimeTokenRefreshSerializer,
    ForgetPasswordSerializer, ResendVerificationSerializer, ChangePasswordSerializer,
    ChangeEmailSerializer, ForgetPasswordConfirmSerializer, LogoutSerializer
)
from .throttles import SendEmailThrottle, LoginThrottle
from ..authentications import CustomAuthentication
from ..models import UserForgetPasswordRequest, UserVerificationRequest


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = LifeTimeTokenObtainSerializer
    throttle_classes = (LoginThrottle,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = LifeTimeTokenRefreshSerializer


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ForgetPasswordAPIView(generics.CreateAPIView):
    throttle_classes = (SendEmailThrottle,)
    queryset = UserForgetPasswordRequest.objects.all()
    serializer_class = ForgetPasswordSerializer


class VerificationConfirmAPIView(generics.GenericAPIView):
    serializer_class = None

    def post(self, request, *args, **kwargs):
        code = kwargs.get('code')
        obj = UserVerificationRequest.objects.filter(is_active=True, used=False, code=code).first()
        if obj:
            obj.used = True
            obj.is_active = False
            obj.save()
            if obj.user:
                user = obj.user
                user.email = obj.email
                user.save()
            return Response({'status': 'success'})
        raise Http404("not found")


class ForgetPasswordConfirmAPIView(generics.GenericAPIView):
    serializer_class = ForgetPasswordConfirmSerializer

    def post(self, request, *args, **kwargs):
        code = kwargs.get('code')
        obj = UserForgetPasswordRequest.objects.filter(is_active=True, used=False, code=code).first()
        if obj:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            password = serializer.validated_data.get('password')
            user = obj.user
            user.set_password(password)
            user.save()
            return Response(serializer.data)
        raise Http404("not found")


class ResendVerificationEmailAPIView(generics.CreateAPIView):
    throttle_classes = (SendEmailThrottle,)
    queryset = UserVerificationRequest.objects.all()
    serializer_class = ResendVerificationSerializer


class ChangePasswordAPIView(generics.GenericAPIView):
    authentication_classes = (SessionAuthentication, CustomAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response()


class ChangeEmailAPIView(generics.GenericAPIView):
    authentication_classes = (SessionAuthentication, CustomAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({})


class LogoutView(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = LogoutSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
