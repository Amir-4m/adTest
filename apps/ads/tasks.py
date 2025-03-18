import logging
from datetime import datetime

from django.utils import timezone

from celery import shared_task

from apps.ads.models import Campaign, Brand

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='enforce_campaign_budget')
def enforce_campaign_budget(self):
    brands = Brand.objects.prefetch_related('campaigns').filter(
        campaigns__status__in=[
            Campaign.CampaignStatus.RUNNING,
            Campaign.CampaignStatus.SCHEDULED,
            Campaign.CampaignStatus.BUDGET_REACHED,
        ]
    ).distinct()
    for brand in brands:
        daily_spend = brand.get_daily_spend()
        monthly_spend = brand.get_monthly_spend()

        if daily_spend >= brand.daily_budget or monthly_spend >= brand.monthly_budget:
            brand.campaigns.filter(status=Campaign.CampaignStatus.RUNNING).update(
                status=Campaign.CampaignStatus.BUDGET_REACHED
            )
        else:
            brand.campaigns.filter(status=Campaign.CampaignStatus.BUDGET_REACHED).update(
                status=Campaign.CampaignStatus.SCHEDULED
            )
    return "Checked and updated brand budgets"


@shared_task(bind=True, name='start_scheduled_campaigns')
def start_scheduled_campaigns(self):
    campaigns = Campaign.objects.filter(status=Campaign.CampaignStatus.SCHEDULED)
    for campaign in campaigns:
        brand_tz = campaign.brand.get_brand_timezone()
        now_utc = timezone.now()
        now_local = now_utc.astimezone(brand_tz)

        if campaign.allowed_start_hour and campaign.allowed_end_hour:
            allowed_start_dt = timezone.make_aware(
                datetime.combine(now_utc.date(), campaign.allowed_start_hour),
                timezone.utc
            )
            allowed_end_dt = timezone.make_aware(
                datetime.combine(now_utc.date(), campaign.allowed_end_hour),
                timezone.utc
            )

            allowed_start_local = allowed_start_dt.astimezone(brand_tz)
            allowed_end_local = allowed_end_dt.astimezone(brand_tz)

            if allowed_start_local > allowed_end_local:
                allowed_end_local += timezone.timedelta(days=1)

            if allowed_start_local <= now_local < allowed_end_local:
                campaign.status = Campaign.CampaignStatus.RUNNING
                campaign.save(update_fields=['status'])
        else:
            # No dayparting defined, start the campaign.
            campaign.status = Campaign.CampaignStatus.RUNNING
            campaign.save(update_fields=['status'])
    return "Scheduled campaigns updated based on dayparting conditions."


@shared_task(bind=True, name='stop_dayparting_campaigns')
def stop_dayparting_campaigns(self):
    # Get running campaigns that have dayparting defined.
    campaigns = Campaign.objects.filter(
        status=Campaign.CampaignStatus.RUNNING,
        allowed_start_hour__isnull=False,
        allowed_end_hour__isnull=False,
    )
    now_utc = timezone.now()

    for campaign in campaigns:
        brand_tz = campaign.brand.get_brand_timezone()
        now_local = now_utc.astimezone(brand_tz)

        # Combine today's UTC date with the allowed times (which are in UTC) to form datetime objects.
        allowed_start_dt = timezone.make_aware(
            datetime.combine(now_utc.date(), campaign.allowed_start_hour),
            timezone.utc
        )
        allowed_end_dt = timezone.make_aware(
            datetime.combine(now_utc.date(), campaign.allowed_end_hour),
            timezone.utc
        )

        # Convert allowed times to the brand's local timezone.
        allowed_start_local = allowed_start_dt.astimezone(brand_tz)
        allowed_end_local = allowed_end_dt.astimezone(brand_tz)

        # Handle case when allowed period crosses midnight.
        if allowed_start_local > allowed_end_local:
            allowed_end_local += timezone.timedelta(days=1)

        # If current local time is outside the allowed window, update the campaign status to SCHEDULED.
        if not (allowed_start_local <= now_local < allowed_end_local):
            campaign.status = Campaign.CampaignStatus.SCHEDULED
            campaign.save(update_fields=['status'])

    return "Stopped dayparting campaigns that are out of allowed time."
