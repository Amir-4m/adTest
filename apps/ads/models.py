import pytz
from dateutil.relativedelta import relativedelta

from django.db import models, transaction
from django.db.models import Sum, F
from django.db.models.functions.comparison import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.users.models import User
from mixins.model_mixins import BaseModelMixin
from utils.db import AtTimeZone


class GlobalAdPricing(BaseModelMixin):
    cost_per_click = models.DecimalField(
        verbose_name=_("Default Cost Per Click"),
        max_digits=10,
        decimal_places=4,
        default=0.05
    )
    cost_per_impression = models.DecimalField(
        verbose_name=_("Default Cost Per 1000 Impressions"),
        max_digits=10,
        decimal_places=2,
        default=2.00
    )
    cost_per_view = models.DecimalField(
        verbose_name=_("Default Cost Per View"),
        max_digits=10,
        decimal_places=4,
        default=0.10
    )
    cost_per_acquisition = models.DecimalField(
        verbose_name=_("Default Cost Per Acquisition"),
        max_digits=10,
        decimal_places=2,
        default=10.00
    )

    class Meta:
        verbose_name = _("Global Ad Pricing")
        verbose_name_plural = _("Global Ad Pricing")

    def __str__(self):
        return _("Global Default Ad Pricing")

    @classmethod
    def get_default_pricing(cls):
        """Retrieve or create the global default pricing."""
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj


class Brand(BaseModelMixin):
    name = models.CharField(
        verbose_name=_("Title"),
        max_length=128,
    )
    daily_budget = models.DecimalField(
        verbose_name=_("Title"),
        max_digits=10,
        decimal_places=2
    )
    monthly_budget = models.DecimalField(
        verbose_name=_("Title"),
        max_digits=10,
        decimal_places=2
    )
    timezone_str = models.CharField(
        verbose_name=_("Title"),
        max_length=50,
        default='UTC'
    )
    owner = models.ForeignKey(
        User,
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
        related_name='brands'
    )
    is_active = models.BooleanField(
        verbose_name=_('Active ?'),
        default=True
    )

    class Meta:
        verbose_name = _("Brand")
        verbose_name_plural = _("Brand")

    def __str__(self):
        return self.name

    def get_brand_timezone(self):
        return pytz.timezone(self.timezone_str)

    def _localize_datetime(self, dt):
        """Converts a datetime object to the brand's timezone."""
        brand_tz = self.get_brand_timezone()
        return dt.astimezone(brand_tz)

    def get_daily_spend(self):
        from apps.payments.models import Transaction

        """Returns the total cost spent today in the brand's timezone."""
        brand_tz = self.get_brand_timezone()
        now = timezone.now().astimezone(brand_tz)  # Localized now()

        return Transaction.objects.annotate(
            local_datetime=AtTimeZone(F('created_at'), brand_tz.zone)
        ).filter(
            brand=self,
            transaction_type=Transaction.TransactionTypeChoices.COST,
            local_datetime__date=now.date()
        ).aggregate(total=Coalesce(Sum('amount'), 0, output_field=models.DecimalField()))['total']

    def get_monthly_spend(self):
        from apps.payments.models import Transaction

        """Returns the total cost spent in the current month in the brand's timezone."""
        brand_tz = self.get_brand_timezone()
        now = timezone.now().astimezone(brand_tz)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # First day of the month
        end_of_month = start_of_month + relativedelta(months=1)

        return Transaction.objects.annotate(
            local_datetime=AtTimeZone(F('created_at'), brand_tz.zone)
        ).filter(
            brand=self,
            transaction_type=Transaction.TransactionTypeChoices.COST,
            local_datetime__gte=start_of_month,
            local_datetime__lt=end_of_month
        ).aggregate(total=Coalesce(Sum('amount'), 0, output_field=models.DecimalField()))['total']


class Campaign(BaseModelMixin):
    class CampaignStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SCHEDULED = 'scheduled', _('Scheduled')
        BUDGET_REACHED = 'budget_reached', _('Budget Reached')
        RUNNING = 'running', _('Running')
        PAUSED = 'paused', _('Paused')
        COMPLETED = 'completed', _('Completed')

    brand = models.ForeignKey(
        Brand,
        verbose_name=_("Brand"),
        on_delete=models.CASCADE,
        related_name='campaigns'
    )
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=14,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100
    )
    is_active = models.BooleanField(
        verbose_name=_("Active?"),
        default=True
    )
    allowed_start_hour = models.TimeField(
        verbose_name=_("Allowed Start Hour"),
        null=True,
        blank=True
    )
    allowed_end_hour = models.TimeField(
        verbose_name=_("Allowed End Hour"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    def __str__(self):
        return self.name

    def start(self):
        self.status = self.CampaignStatus.RUNNING
        self.save()

    def schedule(self):
        self.status = self.CampaignStatus.SCHEDULED
        self.save()

    def budget_reach(self):
        self.status = self.CampaignStatus.BUDGET_REACHED
        self.save()

    def pause(self):
        self.status = self.CampaignStatus.PAUSED
        self.save()

    def complete(self):
        self.status = self.CampaignStatus.COMPLETED
        self.save()


class AdSet(BaseModelMixin):
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_("Campaign"),
        on_delete=models.CASCADE,
        related_name='adsets'
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100
    )
    is_active = models.BooleanField(
        verbose_name=_("Active?"),
        default=True
    )

    class Meta:
        verbose_name = _("Ad Set")
        verbose_name_plural = _("Ad Sets")

    def __str__(self):
        return self.name


class Ad(BaseModelMixin):
    adset = models.ForeignKey(
        AdSet,
        verbose_name=_("Ad Set"),
        on_delete=models.CASCADE,
        related_name='ads'
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100
    )
    is_active = models.BooleanField(
        verbose_name=_("Active?"),
        default=True
    )
    file = models.FileField(
        verbose_name=_("File"),
        upload_to='ads/',
        null=True,
        blank=True
    )
    content = models.TextField(
        verbose_name=_("Content"),
        null=True,
        blank=True
    )

    cost_per_click = models.DecimalField(
        verbose_name=_("Cost Per Click"),
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    cost_per_impression = models.DecimalField(
        verbose_name=_("Cost Per 1000 Impressions"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    cost_per_view = models.DecimalField(
        verbose_name=_("Cost Per View"),
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    cost_per_acquisition = models.DecimalField(
        verbose_name=_("Cost Per Acquisition"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Ad")
        verbose_name_plural = _("Ads")

    def __str__(self):
        return self.name

    def get_cost_per_click(self):
        return self.cost_per_click if self.cost_per_click is not None else GlobalAdPricing.get_default_pricing().cost_per_click

    def get_cost_per_impression(self):
        return self.cost_per_impression if self.cost_per_impression is not None else GlobalAdPricing.get_default_pricing().cost_per_impression

    def get_cost_per_view(self):
        return self.cost_per_view if self.cost_per_view is not None else GlobalAdPricing.get_default_pricing().cost_per_view

    def get_cost_per_acquisition(self):
        return self.cost_per_acquisition if self.cost_per_acquisition is not None else GlobalAdPricing.get_default_pricing().cost_per_acquisition

    def _get_brand_budget_spent(self, brand):
        """ Returns the daily and monthly spend for a brand, ensuring no NULL values using Coalesce. """
        daily_spend = brand.get_daily_spend()
        monthly_spend = brand.get_monthly_spend()
        return daily_spend, monthly_spend

    def _create_transaction_and_check_budget(self, cost, cost_type):
        from apps.payments.models import Transaction

        """
        1. Charge the campaign by creating a transaction.
        2. Then check if the budget is exceeded.
        3. If exceeded, deactivate the campaign.
        """
        campaign = self.adset.campaign
        brand = campaign.brand
        if campaign.status != Campaign.CampaignStatus.RUNNING:
            return False, "Campaign is already paused."

        with transaction.atomic():
            brand = Brand.objects.select_for_update().get(uuid=brand.uuid)

            Transaction.objects.create(
                brand=brand,
                campaign=campaign,
                ad=self,
                amount=cost,
                transaction_type=Transaction.TransactionTypeChoices.COST,
                cost_type=cost_type
            )

            daily_spend, monthly_spend = self._get_brand_budget_spent(brand)
            if daily_spend >= brand.daily_budget or monthly_spend >= brand.monthly_budget:
                Campaign.objects.filter(brand=brand, status=Campaign.CampaignStatus.RUNNING).update(
                    status=Campaign.CampaignStatus.BUDGET_REACHED
                )
                return True, "Transaction created, but all campaigns for this brand are now paused due to budget limit."

        return True, "Transaction created successfully."

    def log_click(self):
        from apps.payments.models import Transaction

        return self._create_transaction_and_check_budget(self.get_cost_per_click(), Transaction.CostTypeChoices.CLICK)

    def log_impression(self):
        from apps.payments.models import Transaction

        return self._create_transaction_and_check_budget(self.get_cost_per_impression() / 1000,
                                                         Transaction.CostTypeChoices.IMPRESSION)

    def log_view(self):
        from apps.payments.models import Transaction

        return self._create_transaction_and_check_budget(self.get_cost_per_view(), Transaction.CostTypeChoices.VIEW)

    def log_acquisition(self):
        from apps.payments.models import Transaction

        return self._create_transaction_and_check_budget(self.get_cost_per_acquisition(),
                                                         Transaction.CostTypeChoices.ACQUISITION)
