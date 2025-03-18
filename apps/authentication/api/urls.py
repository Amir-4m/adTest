from django.urls import path

from .views import (
    RegisterAPIView, CustomTokenObtainPairView, CustomTokenRefreshView,
    ForgetPasswordAPIView, ResendVerificationEmailAPIView, ChangePasswordAPIView,
    ForgetPasswordConfirmAPIView,
    VerificationConfirmAPIView, LogoutView
)

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name="token"),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name="token_refresh"),
    path('register/', RegisterAPIView.as_view(), name="register"),
    path('forget-password/', ForgetPasswordAPIView.as_view(), name="forget-password"),
    path('forget-password/<str:code>/confirm/', ForgetPasswordConfirmAPIView.as_view(), name="forget-password-confirm"),
    path('verification/<str:code>/confirm/', VerificationConfirmAPIView.as_view(), name="verification-confirm"),
    path('change-password/', ChangePasswordAPIView.as_view(), name="change-password"),
    # path('change-email/', ChangeEmailAPIView.as_view(), name="change-email"),
    path('resend-verification/', ResendVerificationEmailAPIView.as_view(), name="resend-verification"),
    path('logout/', LogoutView.as_view(), name="logout"),
]
