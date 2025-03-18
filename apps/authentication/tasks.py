import logging
from celery import shared_task

from apps.authentication.models import UserVerificationRequest, UserForgetPasswordRequest
from apps.authentication.services import AuthenticationService
from apps.users.models import User

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='send_account_verification_email')
def send_account_verification_email(self, user_id, email=None, code=None):
    try:
        user = User.objects.get(pk=user_id)
        if email is None:
            email = user.email
        verification_request, _created = UserVerificationRequest.objects.get_or_create(
            user=user,
            email=email,
            used=False,
            is_active=True,
            defaults={'code': code}
        )
        AuthenticationService.send_verification_email(user, verification_request.code, email)
    except User.DoesNotExist:
        logger.error(f'User with pk {user_id} does not exist')


@shared_task(bind=True, name='send_forget_password_email')
def send_forget_password_email(self, user_id):
    try:
        user = User.objects.get(pk=user_id)
        forget_request, _created = UserForgetPasswordRequest.objects.get_or_create(
            user=user,
            email=user.email,
            used=False,
            is_active=True
        )
        AuthenticationService.send_forget_password_email(user, forget_request.code)
    except User.DoesNotExist:
        logger.error(f'User with pk {user_id} does not exist')
