import decimal
from datetime import time, timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.companies.models import Product, CompanyInventory, UserAvailability, CompanyBookingSettings, \
    CompanyInvitation, Service, CompanyUser, Company
from apps.payments.models import TransactionMethod, UserPaymentSettings, Transaction
from apps.payments.tests.helpers import create_sale, create_payment, create_test_sale_webhook
from apps.permissions.models import CompanyPermission, CompanyTier
from apps.sales.models import Sale, SaleItem
from apps.subscriptions.models import Subscription, SubscriptionItem
from apps.users.models import User
from mixins.model_mixins import AvailabilityModelMixin


class ApprovedCompanyTestCaseMixin(APITestCase):
    fixtures = ['apps/permissions/fixtures/permissions.json']

    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(
            title='Test Company8dlk7',
            time_zone='America/Edmonton',
            is_active=True,
            country='CA',
            state='AB',
            city='Edmonton',
            status=Company.Status.DRAFT
        )
        cls.company.status = Company.Status.APPROVED
        # fetch permissions
        permissions = CompanyPermission.objects.all()
        cls.subscription_item = SubscriptionItem.objects.create(
            subscription_type=0,
            title='Test Subscription',
            price=100,
            description='Test Subscription',
            solution_features=['Test Feature'],
            is_active=True
        )
        cls.subscription_item.permissions.add(*permissions)
        cls.subscription_item.save()
        cls.subscription = Subscription.objects.create(
            company=cls.company,
            subscription_item=cls.subscription_item,
            end_date=timezone.now() + timedelta(days=30),
            is_active=True,
            subtotal_price=100.00,
            total_price=100.00
        )
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        cls.user_2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword'
        )

        # Additional setup for payment-related objects can go here as needed

        cls.company_user = CompanyUser.objects.create(
            company=cls.company,
            user=cls.user,
            is_owner=True,
            is_admin=True,
            first_name='John',
            last_name='Doe',
            role="Owner"
        )
        cls.company_user.set_pin('1234')
        cls.company_user_2 = CompanyUser.objects.create(
            company=cls.company,
            user=cls.user_2,
            is_owner=False,
            is_admin=True,
            first_name='Jane',
            last_name='Smith',
            role="Manager"
        )
        cls.company_user_2.set_pin('2345')
        cls.company.save()

        cls.ct = CompanyTier.objects.create(
            company=cls.company,
            name='Tier 1',
            editable=True,
        )
        cls.ct.company_users.add(cls.company_user)
        permissions = CompanyPermission.objects.all()
        cls.ct.permissions.add(*permissions)
        # Create a service and link it to the company
        cls.service = Service.objects.create(
            description="Test Service",
            price=100,
            duration=timezone.timedelta(minutes=60)
        )
        cls.service.companies.add(cls.company)
        cls.invitation = CompanyInvitation.objects.create(
            company=cls.company,
            email="test2@example.com"
        )
        cls.company_user.user_services.create(
            service=cls.service,
            duration=timezone.timedelta(minutes=30),
            price=decimal.Decimal("100.00"),
            is_active=True
        )
        cls.company_user_2.user_services.create(
            service=cls.service,
            duration=timezone.timedelta(minutes=30),
            price=decimal.Decimal("100.00"),
            is_active=True
        )

        try:
            cls.booking_settings = CompanyBookingSettings.objects.get(company=cls.company)
        except CompanyBookingSettings.DoesNotExist:
            cls.booking_settings = CompanyBookingSettings.objects.create(
                company=cls.company,
                reschedule_allowed_timeframe=CompanyBookingSettings.Timeframes.ONE_HOURS,
                penalty_charge_percentage=10.0,
                accept_online=True,
                accept_walk_in=True,
                max_waiting_time=timezone.timedelta(minutes=15),
                buffer_time=timezone.timedelta(minutes=10),
                prepay_required=False,
                text_confirmation_required=True
            )

        # Define the weekly schedule
        availability_schedule = [
            {"weekday": AvailabilityModelMixin.Weekdays.MONDAY, "start_time": time(9, 0), "end_time": time(17, 0)},
            {"weekday": AvailabilityModelMixin.Weekdays.TUESDAY, "start_time": time(9, 0), "end_time": time(17, 0)},
            {"weekday": AvailabilityModelMixin.Weekdays.WEDNESDAY, "start_time": time(9, 0),
             "end_time": time(17, 0)},
            {"weekday": AvailabilityModelMixin.Weekdays.THURSDAY, "start_time": time(9, 0),
             "end_time": time(17, 0)},
            {"weekday": AvailabilityModelMixin.Weekdays.FRIDAY, "start_time": time(9, 0), "end_time": time(17, 0)},
        ]

        # Loop through the schedule and create UserAvailability instances
        for day in availability_schedule:
            UserAvailability.objects.update_or_create(
                company_user=cls.company_user,
                weekday=day["weekday"],
                defaults=dict(
                    start_time=day["start_time"],
                    end_time=day["end_time"],
                    is_day_off=False
                )
            )
        cls.transaction_method = TransactionMethod.objects.create(
            title='Credit Card',
            company=cls.company,
        )

        cls.product = Product.objects.create(
            title='Sample Product',
            supply_price=100.0,
            retail_price=120.0
        )

        CompanyInventory.objects.create(
            company=cls.company,
            product=cls.product,
            quantity=10,
        )

        # Update UserPaymentSettings for company_user
        UserPaymentSettings.objects.filter(company_user=cls.company_user).update(
            service_general_commission='60%',
            product_general_commission='40%',
            payment_type='commission',
            include_product_commission=True,
        )

        # Update UserPaymentSettings for company_user_2
        UserPaymentSettings.objects.filter(company_user=cls.company_user_2).update(
            service_general_commission='50%',
            product_general_commission='50%',
            payment_type='commission',
            include_product_commission=True,
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def generate_sale(self, sale_info, make_payment=False, is_bos=False):
        items = sale_info['items']
        tip = sale_info['tip']
        client = sale_info.get('client')  # Fetch the client from the payload
        scheduled_for = sale_info.get('scheduled_for')

        sale = create_sale(
            self,
            tip=tip,
            transaction_method=self.transaction_method.pk,
            company=self.company.pk,
            items=items,
            scheduled_for=scheduled_for,
            client=client
        )
        if make_payment:
            sale_date = sale_info['date']
            payment_response = create_payment(
                self,
                sales=[sale["sale_data"]['id']],
                amount=sale["total_amount"],
                transaction_method=self.transaction_method.pk if not is_bos else None,
            )
            self.assertEqual(payment_response['amount'], f'{sale["total_amount"]:.2f}')
            if is_bos:
                create_test_sale_webhook(self, sale["sale_data"]['id'], int(sale["total_amount"] * 100), int(tip * 100))

            # Adjust the created_at date of sale and transactions
            sale_obj = Sale.objects.get(id=sale["sale_data"]['id'])
            sale_obj.created_at = sale_date
            sale_obj.payment_date = sale_date
            sale_obj.save()
            transactions = Transaction.objects.filter(sale=sale_obj)
            for transaction in transactions:
                transaction.created_at = sale_date
                transaction.save()
            sale_items = SaleItem.objects.filter(sale=sale_obj)
            for sale_item in sale_items:
                sale_item.created_at = sale_date
                sale_item.save()
        return sale
