from django.test import TestCase
from apps.ads.models import GlobalAdPricing

from decimal import Decimal
from datetime import time

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.users.models import User
from apps.ads.models import Brand, Campaign, AdSet, Ad
from apps.payments.models import Transaction


class APITestCaseBase(APITestCase):
    """Base test case that creates a test user and sets up an authenticated API client."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)


class AdsModelTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(username="testuser")
        # Create a test brand with budgets and timezone
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
            timezone_str="America/Edmonton",
            owner=self.user,
            is_active=True
        )
        # Create a running campaign with dayparting settings
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=Campaign.CampaignStatus.RUNNING,
            is_active=True,
            allowed_start_hour=time(8, 0),
            allowed_end_hour=time(20, 0)
        )
        # Create an ad set for the campaign
        self.adset = AdSet.objects.create(
            campaign=self.campaign,
            name="Test AdSet",
            is_active=True
        )
        # Create an ad with its own cost settings
        self.ad = Ad.objects.create(
            adset=self.adset,
            name="Test Ad",
            is_active=True,
            cost_per_click=Decimal("0.10"),
            cost_per_impression=Decimal("2.00"),  # per 1000 impressions
            cost_per_view=Decimal("0.05"),
            cost_per_acquisition=Decimal("5.00")
        )
        self.global_pricing = GlobalAdPricing.get_default_pricing()

    def test_global_pricing_default(self):
        self.assertIsNotNone(self.global_pricing)
        self.assertEqual(self.global_pricing.cost_per_click, 0.05)

    def test_brand_spending(self):
        now = timezone.now()
        Transaction.objects.create(
            brand=self.brand,
            campaign=self.campaign,
            ad=self.ad,
            amount=Decimal("10.00"),
            transaction_type=Transaction.TransactionTypeChoices.COST,
            cost_type=Transaction.CostTypeChoices.CLICK,
            created_at=now
        )
        daily_spend = self.brand.get_daily_spend()
        self.assertEqual(daily_spend, Decimal("10.00"))
        monthly_spend = self.brand.get_monthly_spend()
        self.assertEqual(monthly_spend, Decimal("10.00"))

    def test_ad_log_click_creates_transaction(self):
        initial_tx_count = Transaction.objects.count()
        result, message = self.ad.log_click()
        self.assertTrue(result)
        self.assertEqual(Transaction.objects.count(), initial_tx_count + 1)
        tx = Transaction.objects.last()
        self.assertEqual(tx.cost_type, Transaction.CostTypeChoices.CLICK)
        self.assertEqual(tx.amount, self.ad.get_cost_per_click())

    def test_budget_enforcement(self):
        self.brand.daily_budget = Decimal("0.05")
        self.brand.save()
        result, message = self.ad.log_click()  # This click should cost 0.10, exceeding budget.
        self.assertTrue(result)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.CampaignStatus.BUDGET_REACHED)

    def test_dayparting_start_task(self):
        self.campaign.status = Campaign.CampaignStatus.SCHEDULED
        self.campaign.allowed_start_hour = time(0, 0)
        self.campaign.allowed_end_hour = time(23, 59)
        self.campaign.save()
        from apps.ads.tasks import start_scheduled_campaigns
        start_scheduled_campaigns()
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.CampaignStatus.RUNNING)

    def test_dayparting_stop_task(self):
        self.campaign.status = Campaign.CampaignStatus.RUNNING
        self.campaign.allowed_start_hour = time(0, 0)
        self.campaign.allowed_end_hour = time(1, 0)
        self.campaign.save()
        from apps.ads.tasks import stop_dayparting_campaigns
        stop_dayparting_campaigns()
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.CampaignStatus.SCHEDULED)


class BrandAPITest(APITestCaseBase):
    def setUp(self):
        super().setUp()
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
            timezone_str="UTC",
            owner=self.user,
            is_active=True
        )

    def test_get_brands(self):
        url = reverse("brands-api-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only brands for the authenticated user should be returned.
        self.assertEqual(len(response.data['results']), 1)

    def test_create_brand(self):
        url = reverse("brands-api-list")
        data = {
            "name": "New Brand",
            "daily_budget": "50.00",
            "monthly_budget": "500.00",
            "timezone_str": "UTC",
            "owner": self.user.id,
            "is_active": True
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Brand")

    def test_update_brand(self):
        url = reverse("brands-api-detail", args=[self.brand.uuid])
        data = {
            "name": "Updated Brand",
            "daily_budget": "150.00",
            "monthly_budget": "1500.00",
            "timezone_str": "UTC",
            "owner": self.user.id,
            "is_active": True
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.name, "Updated Brand")


class CampaignAPITest(APITestCaseBase):
    def setUp(self):
        super().setUp()
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
            timezone_str="UTC",
            owner=self.user,
            is_active=True
        )
        # Start with a DRAFT campaign, which can be updated.
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=Campaign.CampaignStatus.DRAFT,
            is_active=True
        )

    def test_get_campaigns(self):
        url = reverse("campaigns-api-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only campaigns belonging to brands owned by the user should be returned.
        self.assertEqual(len(response.data['results']), 1)

    def test_create_campaign(self):
        url = reverse("campaigns-api-list")
        data = {
            "brand": self.brand.uuid,
            "name": "New Campaign",
            "status": Campaign.CampaignStatus.DRAFT,
            "is_active": True
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Campaign")


class AdSetAPITest(APITestCaseBase):
    def setUp(self):
        super().setUp()
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
            timezone_str="UTC",
            owner=self.user,
            is_active=True
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=Campaign.CampaignStatus.DRAFT,
            is_active=True
        )
        self.adset = AdSet.objects.create(
            campaign=self.campaign,
            name="Test AdSet",
            is_active=True
        )

    def test_get_adsets(self):
        url = reverse("ad-sets-api-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_adset(self):
        url = reverse("ad-sets-api-list")
        data = {
            "campaign": self.campaign.uuid,
            "name": "New AdSet",
            "is_active": True
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New AdSet")


class AdAPITest(APITestCaseBase):
    def setUp(self):
        super().setUp()
        self.brand = Brand.objects.create(
            name="Test Brand",
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
            timezone_str="UTC",
            owner=self.user,
            is_active=True
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Test Campaign",
            status=Campaign.CampaignStatus.DRAFT,
            is_active=True
        )
        self.adset = AdSet.objects.create(
            campaign=self.campaign,
            name="Test AdSet",
            is_active=True
        )
        self.ad = Ad.objects.create(
            adset=self.adset,
            name="Test Ad",
            is_active=True,
            cost_per_click=Decimal("0.10"),
            cost_per_impression=Decimal("2.00"),
            cost_per_view=Decimal("0.05"),
            cost_per_acquisition=Decimal("5.00")
        )

    def test_get_ads(self):
        url = reverse("ads-api-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_ad(self):
        url = reverse("ads-api-list")
        data = {
            "adset": self.adset.uuid,
            "name": "New Ad",
            "is_active": True,
            "cost_per_click": "0.15",
            "cost_per_impression": "2.50",
            "cost_per_view": "0.07",
            "cost_per_acquisition": "6.00"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Ad")
