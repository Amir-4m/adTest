from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.ads.models import Brand, Campaign, Ad
from mixins.model_mixins import BaseModelMixin


class Transaction(BaseModelMixin):
    class TransactionTypeChoices(models.TextChoices):
        COST = 'cost', _('Cost')
        PAYMENT = 'payment', _('Payment')

    class CostTypeChoices(models.TextChoices):
        CLICK = 'click', _('Click')
        IMPRESSION = 'impression', _('Impression')
        VIEW = 'view', _('View')
        ACQUISITION = 'acquisition', _('Acquisition')

    brand = models.ForeignKey(
        Brand,
        verbose_name=_("Brand"),
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_("Campaign"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions'
    )
    ad = models.ForeignKey(
        Ad,
        verbose_name=_("Ad"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions'
    )
    amount = models.DecimalField(
        verbose_name=_("Amount"),
        max_digits=10,
        decimal_places=4
    )
    transaction_type = models.CharField(
        verbose_name=_("Transaction Type"),
        max_length=10,
        choices=TransactionTypeChoices.choices
    )
    cost_type = models.CharField(
        verbose_name=_("Cost Type"),
        max_length=15,
        choices=CostTypeChoices.choices,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.get_cost_type_display()} - {self.amount}"
