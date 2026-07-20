from datetime import date, datetime

CURRENCY_ALIASES = {
    "USD": "USD",
    "US DOLLAR": "USD",
    "US$": "USD",
    "EUR": "EUR",
    "€": "EUR",
    "ILS": "ILS",
    "NIS": "ILS",
    "GBP": "GBP",
    "£": "GBP",
}

PAYMENT_METHOD_ALIASES = {
    "corporate card": "Corporate Card",
    "corp card": "Corporate Card",
    "credit card": "Credit Card",
    "cc": "Credit Card",
    "direct debit": "Direct Debit",
    "dd": "Direct Debit",
    "bank transfer": "Bank Transfer",
    "bank xfer": "Bank Transfer",
    "wire transfer": "Wire Transfer",
    "wire": "Wire Transfer",
}

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]


def normalize_currency(raw: str | None) -> str | None:
    if not raw or not raw.strip():
        return None
    key = raw.strip().upper()
    if key in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[key]
    if len(key) == 3 and key.isalpha():
        return key
    return None


def normalize_payment_method(raw: str | None) -> str | None:
    if not raw or not raw.strip():
        return None
    key = raw.strip().lower()
    return PAYMENT_METHOD_ALIASES.get(key, raw.strip().title())


def parse_date(raw: str | None) -> date | None:
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = raw.strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def clean_text(raw: str | None) -> str | None:
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None
