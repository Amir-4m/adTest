import random

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from mixins.model_mixins import BaseModelMixin
from apps.users.models import User
from .utils import create_tracking_code_with_uuid


class UserRequestMixin(BaseModelMixin):
    code = models.CharField(
        verbose_name=_('Code'),
        default=create_tracking_code_with_uuid,
        max_length=16,
        editable=False
    )
    email = models.EmailField(
        verbose_name=_('email'),
        null=True,
        blank=False,
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{10,15}$',
        message='Phone number must be entered in the format: "+999999999". Up to 15 digits is allowed.'
    )
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=17,
        validators=[phone_regex],
        null=True
    )
    user = models.ForeignKey(
        verbose_name=_('User'),
        to=User,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )
    used = models.BooleanField(
        verbose_name=_('Used'),
        default=False
    )
    is_active = models.BooleanField(
        verbose_name=_('Active?'),
        default=True,
    )

    @property
    def user_email(self):
        return self.user.email

    class Meta:
        abstract = True


class UserVerificationRequest(UserRequestMixin):
    class Meta:
        verbose_name = _('User Verification Request')
        verbose_name_plural = _('Users Verification Requests')


class UserForgetPasswordRequest(UserRequestMixin):
    class Meta:
        verbose_name = _('User Forget Password Request')
        verbose_name_plural = _('Users Forget Password Requests')
