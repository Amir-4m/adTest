import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from mixins.model_mixins import BaseModelMixin, UserInfoModelMixin


def upload_user_image(instance, filename):
    return f'users/images/{instance.pk}.{filename.split(".")[-1]}'


class User(BaseModelMixin, AbstractUser, UserInfoModelMixin):
    __doc__ = _("""
    Contains User Information
    """)
    logo = models.ImageField(
        _('Logo'),
        upload_to=upload_user_image,
        null=True,
        blank=True
    )
    email = models.EmailField(
        _('email address'),
        unique=True
    )
    uuid = models.UUIDField(
        _('UUID'),
        default=uuid.uuid4
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f'{self.first_name} {self.last_name}-{self.email}'
