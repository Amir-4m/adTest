from django.contrib.auth.models import User

from apps.authentication.models import UserVerificationRequest


class AuthenticationService(object):
    @staticmethod
    def is_verified(email):
        verification = UserVerificationRequest.objects.filter(email__icontains=email, used=True,
                                                              is_active=False).order_by('-created_at').first()
        return verification is not None

    @staticmethod
    def email_exists(email):
        return User.objects.filter(email__icontains=email).exists()

    @staticmethod
    def send_verification_email(user, code, email=None):
        ...

    @staticmethod
    def send_phone_verification_sms(user, code, phone_number):
        ...

    @staticmethod
    def send_forget_password_email(user, code):
        ...
