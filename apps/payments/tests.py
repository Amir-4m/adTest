from django.test import TestCase
from django.utils import timezone
from decimal import Decimal

from apps.users.models import User
from apps.ads.models import Brand, Campaign, AdSet, Ad
from apps.payments.models import Transaction


class PaymentsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="paymenttester")
        self.brand = Brand.objects.create(
            name="Payment Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
            timezone_str="UTC",
            owner=self.user,
            is_active=True
        )
        # Create a running campaign
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Payment Campaign",
            status=Campaign.CampaignStatus.RUNNING,
            is_active=True
        )
        self.adset = AdSet.objects.create(
            campaign=self.campaign,
            name="Payment AdSet",
            is_active=True
        )
        self.ad = Ad.objects.create(
            adset=self.adset,
            name="Payment Ad",
            is_active=True,
            cost_per_click=Decimal("0.10"),
            cost_per_impression=Decimal("2.00"),
            cost_per_view=Decimal("0.05"),
            cost_per_acquisition=Decimal("5.00")
        )

    def test_transaction_str(self):
        tx = Transaction.objects.create(
            brand=self.brand,
            campaign=self.campaign,
            ad=self.ad,
            amount=Decimal("0.10"),
            transaction_type=Transaction.TransactionTypeChoices.COST,
            cost_type=Transaction.CostTypeChoices.CLICK
        )
        expected_str = f"{tx.get_transaction_type_display()} - {tx.get_cost_type_display()} - {tx.amount}"
        self.assertEqual(str(tx), expected_str)

    def test_multiple_transactions_aggregation(self):
        now = timezone.now()
        Transaction.objects.create(
            brand=self.brand,
            campaign=self.campaign,
            ad=self.ad,
            amount=Decimal("5.00"),
            transaction_type=Transaction.TransactionTypeChoices.COST,
            cost_type=Transaction.CostTypeChoices.VIEW,
            created_at=now
        )
        Transaction.objects.create(
            brand=self.brand,
            campaign=self.campaign,
            ad=self.ad,
            amount=Decimal("7.00"),
            transaction_type=Transaction.TransactionTypeChoices.COST,
            cost_type=Transaction.CostTypeChoices.IMPRESSION,
            created_at=now
        )
        daily_spend = self.brand.get_daily_spend()
        self.assertEqual(daily_spend, Decimal("12.00"))
