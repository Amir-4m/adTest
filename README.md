# 🚀 How to Run or Execute the Code

This guide provides step-by-step instructions to set up, run, and execute the advertising system.

---

## **1️⃣ Prerequisites**

Ensure you have the following installed:

- **Python 3.8+**
- **Django 4+**
- **PostgreSQL** (Recommended, but SQLite can be used for testing)
- **Redis** (For Celery task queue)
- **Celery** (For scheduled background tasks)
- **Celery Beat** (For periodic tasks)

---

## **2️⃣ Setup the Project**

### **Clone the Repository**

```bash
git clone git@github.com:Amir-4m/adTest.git
cd adTest
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows
pip install -r requirements.txt
```

## **3️⃣ Configure the Database**

### **Update .env File**

```yaml
DB_NAME=adtest
DB_USER=postgres
DB_PASSWORD=password
DB_ENGINE=django.db.backends.postgresql_psycopg2
DB_HOST=localhost
DB_PORT=5432
DEBUG=True
SECRET_KEY="397@^%w%c2nji+rkp62u#n1!8b%4on22b@1o*w-zh=0_x2x&5e"
REDIS_URL=redis://localhost:6379/
```

### **Update .env File**

``python manage.py makemigrations
``

``python manage.py migrate``

## **4️⃣ Configure the Database**

``python manage.py createsuperuser
``

## **5️⃣ Start the Development Server**

``python manage.py runserver
``
Visit http://127.0.0.1:8000/admin/ to access the Django admin panel.

## **6️⃣ Start Celery Workers**

Celery is required for background tasks like enforcing budgets and handling dayparting.

### **Start Redis (If not already running)**

```bash
redis-server  # On Mac/Linux
redis-server.exe  # On Windows (if installed)
celery -A adTest worker --loglevel=info
celery -A adTest beat --loglevel=info
```

## **7️⃣ Running Tests**

``python manage.py test apps/*``

# Data Structures

## Global Pricing Settings

### GlobalAdPricing

**Attributes:**

- Default cost per click
- Default cost per 1000 impressions
- Default cost per view
- Default cost per acquisition

**Purpose:** Provide fallback pricing values if an individual ad does not define its own.

---

## Brand

**Attributes:**

- Name
- Daily budget
- Monthly budget
- Timezone (as a string)
- Owner (user reference)
- Active flag

**Methods:**

- **`get_daily_spend()`**
    - Aggregate all cost transactions for the current day using the brand’s timezone (by converting transaction
      timestamps to the brand’s local time).

- **`get_monthly_spend()`**
    - Aggregate all cost transactions for the current month, again using the brand’s timezone.

---

## Campaign

**Attributes:**

- Reference to a Brand
- Name
- Status (values: `DRAFT`, `SCHEDULED`, `RUNNING`, `PAUSED`, `BUDGET_REACHED`, `COMPLETED`)
- Allowed start and end times (for dayparting, stored in UTC)

**Methods:**

- **`start()`** → Set status to `RUNNING`
- **`pause()`** → Set status to `PAUSED`
- **`budget_reach()`** → Set status to `BUDGET_REACHED`
- **`schedule()`** → Set status to `SCHEDULED`
- **`complete()`** → Set status to `COMPLETED`

---

## AdSet

**Attributes:**

- Belongs to a Campaign
- Name
- Active flag

---

## Ad

**Attributes:**

- Belongs to an AdSet
- Name
- Active flag
- Media file and text content
- Cost parameters (`click`, `impression`, `view`, `acquisition`)

**Methods:**

- **`get_effective_cost()`**
    - Return the ad’s own cost if set; otherwise, fallback to GlobalAdPricing.

- **`log_event(event_type)`**
    1. When a user interaction occurs (`click`, `impression`, `view`, or `acquisition`), calculate the cost based on the
       event type and create a cost transaction.
    2. After logging the transaction, aggregate the brand’s current spending.
    3. If the brand’s spending exceeds its daily or monthly budget, update all active campaigns for that brand to
       a `Budget Reached` state.

---

## Transaction

**Attributes:**

- References to **Brand, Campaign, and optionally Ad**
- Amount charged
- Transaction type (e.g., `COST` or `PAYMENT`)
- Cost type (e.g., `CLICK`, `IMPRESSION`, `VIEW`, `ACQUISITION`)
- Timestamp (with creation time, later converted to brand local time for filtering)

---

# Key Workflow Steps

## Logging Ad Events and Budget Check

**When an ad event occurs:**

1. Determine the event type (`click`, `impression`, `view`, or `acquisition`).
2. Calculate the cost using the ad’s defined cost or the global default.
3. Create a **Transaction** record for the cost event.
4. Aggregate the **brand’s spending** for the day and month by converting each transaction’s timestamp into the brand’s
   local time.
5. **If spending exceeds the brand’s daily or monthly budget**, update the status of all currently running campaigns
   under that brand to **“Budget Reached.”**

---

## Scheduled Tasks for Budget Enforcement and Dayparting

### **Budget Enforcement Task**

_Periodically (e.g., every 5 minutes), for each brand that has active campaigns:_

1. Use the **brand methods** to calculate daily and monthly spending.
2. If spending is **over budget**, mark running campaigns as **“Budget Reached.”**
3. If spending is **under budget**, reset campaigns from **“Budget Reached”** back to **“Scheduled.”**

---

### **Dayparting Start Task**

_Periodically scan campaigns with a “Scheduled” status:_

1. For campaigns with **allowed start/end times** (stored in UTC), combine the current **UTC date** with these times.
2. Convert these allowed times to the **brand’s local timezone**.
3. **If the current local time falls within the allowed window**, update the campaign’s status to **“Running.”**
4. For campaigns **without dayparting settings**, simply set them to **“Running.”**

---

### **Dayparting Stop Task**

_Periodically scan campaigns that are “Running” and use dayparting:_

1. Convert the campaign’s **allowed start/end times** (combined with the current UTC date) into the **brand’s local time
   **.
2. **If the current local time falls outside the allowed window**, update the campaign’s status to **“Scheduled”** (or a
   paused state).

---

## **Budget Reset (Daily/Monthly)**

- **At the start of a new day or new month**, spending totals are recalculated naturally via the **aggregation methods
  in the Brand model**.
- **Campaigns may then be re-enabled** if the new aggregated spend is below the budget thresholds.

# High-Level Pseudo-code

```yaml
DATA STRUCTURES:
  GlobalAdPricing: { cost_per_click, cost_per_impression, cost_per_view, cost_per_acquisition }
  Brand: { name, daily_budget, monthly_budget, timezone, owner, is_active }
  Campaign: { brand, name, status, allowed_start_hour, allowed_end_hour }
  AdSet: { campaign, name, is_active }
  Ad: { adset, name, is_active, media_file, content, cost parameters }
  Transaction: { brand, campaign, ad, amount, transaction_type, cost_type, created_at }

WORKFLOW:
  FUNCTION log_ad_event(ad, event_type):
    cost = ad.get_effective_cost(event_type)
    CREATE Transaction with cost, event_type, and timestamp
    brand = ad.adset.campaign.brand
    daily_spend = brand.get_daily_spend()
    monthly_spend = brand.get_monthly_spend()
    IF daily_spend OR monthly_spend exceeds budget:
      UPDATE all running campaigns of brand -> status = BUDGET_REACHED
    ENDIF

  TASK enforce_brand_budget:
    FOR each brand with active campaigns:
      daily_spend = brand.get_daily_spend()
      monthly_spend = brand.get_monthly_spend()
      IF daily_spend OR monthly_spend exceeds budget:
        UPDATE running campaigns -> status = BUDGET_REACHED
      ELSE:
        UPDATE campaigns with status BUDGET_REACHED -> status = SCHEDULED
      ENDIF
    ENDFOR

  TASK start_scheduled_campaigns:
    FOR each campaign with status SCHEDULED:
      IF campaign has dayparting settings:
        allowed_start = Convert(UTC_date + allowed_start_hour) to brand local time
        allowed_end = Convert(UTC_date + allowed_end_hour) to brand local time
        IF allowed period spans midnight:
          Adjust allowed_end by adding 1 day
        ENDIF
        IF current brand local time is within allowed period:
          UPDATE campaign -> status = RUNNING
        ENDIF
      ELSE:
        UPDATE campaign -> status = RUNNING
      ENDIF
    ENDFOR

  TASK stop_dayparting_campaigns:
    FOR each campaign with status RUNNING and dayparting settings:
      Convert allowed times to brand local time (handle midnight crossing)
      IF current brand local time is outside allowed period:
        UPDATE campaign -> status = SCHEDULED
      ENDIF
    ENDFOR

  DAILY/MONTHLY RESET:
    (Implicit via recalculation in brand.get_daily_spend() and get_monthly_spend())
    Campaigns are re-enabled if spending falls below budget thresholds.

```