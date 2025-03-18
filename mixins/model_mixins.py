import uuid
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModelMixin(models.Model):
    __doc__ = _("Base Model includes `created_at` and `updated_at`.")
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4
    )
    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True,
        editable=False,
        help_text=_("Timestamp when the object was created.")
    )
    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True,
        editable=False
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class UserInfoModelMixin(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHER = 'other', _('Other')

    gender = models.CharField(
        _('Gender'),
        max_length=6,
        choices=GenderChoices.choices,
        default=GenderChoices.MALE,
        null=True
    )

    email = models.EmailField(
        verbose_name=_("Email"),
        null=True,
        blank=True
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

    class Meta:
        abstract = True


class AddressModelMixin(models.Model):
    address = models.TextField(
        _("Address")
    )
    city = models.CharField(
        _("City"),
        max_length=64,
        blank=True,
        null=True
    )
    state = models.CharField(
        _("State"),
        max_length=32,
        blank=True,
        null=True
    )
    country = models.CharField(
        _("Country"),
        max_length=32,
        blank=True,
        null=True
    )
    postal_code = models.CharField(
        _("Postal Code"),
        max_length=32,
        blank=True,
        null=True
    )

    class Meta:
        abstract = True


class BillingAddressModelMixin(models.Model):
    billing_address = models.TextField(
        _("Billing Address"),
        null=True
    )
    billing_city = models.CharField(
        _("Billing City"),
        max_length=64,
        blank=True,
        null=True
    )
    billing_state = models.CharField(
        _("Billing State"),
        max_length=32,
        blank=True,
        null=True
    )
    billing_country = models.CharField(
        _("Billing Country"),
        max_length=32,
        blank=True,
        null=True
    )
    billing_postal_code = models.CharField(
        _("Billing Postal Code"),
        max_length=32,
        blank=True,
        null=True
    )

    class Meta:
        abstract = True
