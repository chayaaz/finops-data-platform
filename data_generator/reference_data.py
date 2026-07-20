"""Static reference/master data used to generate the synthetic FinOps dataset."""

BUSINESS_ENTITIES = [
    {"name": "FinOps Israel Ltd", "legal_name": "FinOps Israel Ltd.", "country": "Israel", "base_currency": "ILS"},
    {"name": "FinOps US Inc", "legal_name": "FinOps US Inc.", "country": "United States", "base_currency": "USD"},
    {"name": "FinOps Europe GmbH", "legal_name": "FinOps Europe GmbH", "country": "Germany", "base_currency": "EUR"},
]

DEPARTMENTS = [
    ("R&D", "RND"),
    ("Marketing", "MKT"),
    ("HR", "HR"),
    ("IT", "IT"),
    ("Sales", "SLS"),
    ("Customer Success", "CS"),
    ("Finance", "FIN"),
    ("Operations", "OPS"),
]

REGIONS = [
    ("UK", "United Kingdom"),
    ("EU-CENTRAL", "Central Europe"),
    ("US-WEST", "US West Coast"),
    ("US-EAST", "US East Coast"),
    ("GLOBAL", "Global / Remote"),
    ("IL", "Israel"),
]

CURRENCIES = ["USD", "EUR", "ILS"]

# category_tree: parent -> [(child_name, min_amount, max_amount), ...]
CATEGORY_TREE = {
    "Cloud & Infrastructure": [
        ("Cloud Infrastructure", 150, 9000),
        ("Monitoring", 80, 1500),
        ("Hosting & CDN", 60, 2500),
        ("Data & Analytics Platforms", 200, 6000),
    ],
    "Software & Subscriptions": [
        ("SaaS Subscriptions", 30, 3000),
        ("CRM", 100, 4500),
        ("Productivity Software", 20, 1200),
        ("Security Software", 150, 5000),
    ],
    "Marketing & Growth": [
        ("Marketing", 100, 8000),
        ("Advertising", 200, 15000),
        ("Events & Sponsorships", 500, 20000),
        ("Market Research", 300, 6000),
    ],
    "Travel & Facilities": [
        ("Travel & Meals", 20, 2500),
        ("Office Supplies", 10, 800),
        ("Utilities", 100, 3000),
        ("Facilities & Rent", 1000, 25000),
    ],
    "Hardware & Equipment": [
        ("Hardware", 150, 6000),
        ("IT Equipment", 100, 4000),
        ("Office Equipment", 50, 2000),
    ],
    "Professional Services": [
        ("Legal & Compliance", 300, 12000),
        ("Consulting", 500, 20000),
        ("Recruiting", 200, 9000),
        ("Training & Education", 100, 4000),
    ],
    "People & Operations": [
        ("Payroll Services", 1000, 30000),
        ("Benefits Administration", 200, 8000),
        ("Insurance", 300, 10000),
        ("Shipping & Logistics", 30, 3000),
    ],
}

# vendor_name -> (default_category, contract_type)
# contract_type: "Reserved Commitment" | "Annual Contract" | "Monthly Subscription" | "Ad-Hoc"
VENDORS = {
    "Google Cloud": ("Cloud Infrastructure", "Reserved Commitment"),
    "Microsoft Azure": ("Cloud Infrastructure", "Reserved Commitment"),
    "Amazon Web Services": ("Cloud Infrastructure", "Reserved Commitment"),
    "DigitalOcean": ("Cloud Infrastructure", "Monthly Subscription"),
    "Datadog": ("Monitoring", "Annual Contract"),
    "New Relic": ("Monitoring", "Annual Contract"),
    "Grafana Labs": ("Monitoring", "Monthly Subscription"),
    "Cloudflare": ("Hosting & CDN", "Annual Contract"),
    "Fastly": ("Hosting & CDN", "Monthly Subscription"),
    "Snowflake": ("Data & Analytics Platforms", "Reserved Commitment"),
    "Databricks": ("Data & Analytics Platforms", "Annual Contract"),
    "Slack Technologies": ("SaaS Subscriptions", "Annual Contract"),
    "Atlassian": ("SaaS Subscriptions", "Annual Contract"),
    "Notion Labs": ("SaaS Subscriptions", "Monthly Subscription"),
    "Zoom Video": ("SaaS Subscriptions", "Annual Contract"),
    "Salesforce": ("CRM", "Annual Contract"),
    "HubSpot": ("CRM", "Annual Contract"),
    "Pipedrive": ("CRM", "Monthly Subscription"),
    "Microsoft 365": ("Productivity Software", "Annual Contract"),
    "Google Workspace": ("Productivity Software", "Annual Contract"),
    "Adobe": ("Productivity Software", "Annual Contract"),
    "Okta": ("Security Software", "Annual Contract"),
    "CrowdStrike": ("Security Software", "Annual Contract"),
    "1Password": ("Security Software", "Monthly Subscription"),
    "Meta Ads": ("Advertising", "Ad-Hoc"),
    "Google Ads": ("Advertising", "Ad-Hoc"),
    "LinkedIn Marketing": ("Advertising", "Ad-Hoc"),
    "Mailchimp": ("Marketing", "Monthly Subscription"),
    "Hootsuite": ("Marketing", "Monthly Subscription"),
    "Nielsen Research": ("Market Research", "Ad-Hoc"),
    "Gartner": ("Market Research", "Annual Contract"),
    "Booking.com Business": ("Travel & Meals", "Ad-Hoc"),
    "Uber for Business": ("Travel & Meals", "Ad-Hoc"),
    "Delta Airlines": ("Travel & Meals", "Ad-Hoc"),
    "Amazon Business": ("Office Supplies", "Ad-Hoc"),
    "Staples": ("Office Supplies", "Ad-Hoc"),
    "Israel Electric Corp": ("Utilities", "Ad-Hoc"),
    "E.ON Energy": ("Utilities", "Ad-Hoc"),
    "WeWork": ("Facilities & Rent", "Annual Contract"),
    "Regus": ("Facilities & Rent", "Annual Contract"),
    "Dell Technologies": ("Hardware", "Ad-Hoc"),
    "Apple Business": ("Hardware", "Ad-Hoc"),
    "Lenovo": ("Hardware", "Ad-Hoc"),
    "Cisco Systems": ("IT Equipment", "Ad-Hoc"),
    "Herman Miller": ("Office Equipment", "Ad-Hoc"),
    "Herzog Fox & Neeman": ("Legal & Compliance", "Ad-Hoc"),
    "Deloitte Consulting": ("Consulting", "Ad-Hoc"),
    "McKinsey & Company": ("Consulting", "Ad-Hoc"),
    "LinkedIn Talent Solutions": ("Recruiting", "Annual Contract"),
    "Udemy Business": ("Training & Education", "Annual Contract"),
    "Coursera for Business": ("Training & Education", "Annual Contract"),
    "ADP Payroll": ("Payroll Services", "Annual Contract"),
    "Migdal Insurance": ("Insurance", "Annual Contract"),
    "DHL Express": ("Shipping & Logistics", "Ad-Hoc"),
    "FedEx": ("Shipping & Logistics", "Ad-Hoc"),
}

# canonical payment method -> list of dirty text variants seen in raw uploads
PAYMENT_METHOD_VARIANTS = {
    "Corporate Card": ["Corporate Card", "corporate card", "CORP CARD"],
    "Credit Card": ["Credit Card", "CC", "credit card"],
    "Direct Debit": ["Direct Debit", "direct debit", "DD"],
    "Bank Transfer": ["Bank Transfer", "bank xfer", "BANK TRANSFER"],
    "Wire Transfer": ["Wire Transfer", "wire", "WIRE TRANSFER"],
}

# canonical currency code -> list of dirty text variants seen in raw uploads
CURRENCY_VARIANTS = {
    "USD": ["USD", "US DOLLAR", "usd"],
    "EUR": ["EUR", "€", "eur"],
    "ILS": ["ILS", "NIS", "ils"],
}

APPROVAL_STATUSES = ["Pending", "Approved", "Paid", "Rejected"]

ITEM_TYPES = ["Services", "Goods"]

UNITS_OF_MEASURE = ["hour", "license", "unit", "GB", "seat", "month"]

CREATED_BY_USERS = ["system_upload", "finance_user", "ops_user", "procurement_bot"]

SEED_USERS = [
    {"email": "admin@finops-platform.io", "full_name": "Admin User", "role": "admin", "password": "Admin123!"},
    {"email": "dana.cohen@finops-platform.io", "full_name": "Dana Cohen", "role": "finance_manager", "password": "Finance123!"},
    {"email": "yossi.levi@finops-platform.io", "full_name": "Yossi Levi", "role": "finance_manager", "password": "Finance123!"},
    {"email": "maya.shapira@finops-platform.io", "full_name": "Maya Shapira", "role": "analyst", "password": "Analyst123!"},
    {"email": "tom.baker@finops-platform.io", "full_name": "Tom Baker", "role": "analyst", "password": "Analyst123!"},
    {"email": "noa.avraham@finops-platform.io", "full_name": "Noa Avraham", "role": "analyst", "password": "Analyst123!"},
    {"email": "ilan.gross@finops-platform.io", "full_name": "Ilan Gross", "role": "auditor", "password": "Auditor123!"},
]
