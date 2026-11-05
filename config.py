"""
Configuration module for Family Expense Bot.
Defines family members, categories, sheet layout, and phone mapping.
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Family members matching the Google Sheet "Paid By" column
PEOPLE = ["Tanmay", "Akshat", "Aai", "Dad"]

# Aliases mapping variants to canonical name
NAME_ALIASES = {
    "mom": "Aai",
    "aai": "Aai",
    "maa": "Aai",
    "mother": "Aai",
    "dad": "Dad",
    "father": "Dad",
    "papa": "Dad",
    "baba": "Dad",
    "tanmay": "Tanmay",
    "akshat": "Akshat",
}

def normalize_person(name: str) -> str:
    """Maps any casing/alias (e.g. 'mom', 'aai', 'papa') to the canonical name."""
    cleaned = name.strip()
    lowered = cleaned.lower()
    if lowered in NAME_ALIASES:
        return NAME_ALIASES[lowered]
    for person in PEOPLE:
        if person.lower() == lowered:
            return person
    return cleaned.title() or "Unknown"

def get_phone_to_person_map() -> dict[str, str]:
    """
    Builds the phone-to-person mapping from environment variables.
    Phone numbers in Meta Cloud API arrive in international format without '+' (e.g., '919876543210').
    """
    mapping = {}
    phone_tanmay = os.getenv("PHONE_TANMAY", "").strip().replace("+", "").replace(" ", "")
    phone_akshat = os.getenv("PHONE_AKSHAT", "").strip().replace("+", "").replace(" ", "")
    phone_aai = os.getenv("PHONE_AAI", "").strip().replace("+", "").replace(" ", "")
    phone_dad = os.getenv("PHONE_DAD", "").strip().replace("+", "").replace(" ", "")

    if phone_tanmay:
        mapping[phone_tanmay] = "Tanmay"
    if phone_akshat:
        mapping[phone_akshat] = "Akshat"
    if phone_aai:
        mapping[phone_aai] = "Aai"
    if phone_dad:
        mapping[phone_dad] = "Dad"

    return mapping

# Master category list from your Google Sheet dropdown
CATEGORIES = [
    "Medical & Healthcare",
    "Housing & Utilities",
    "Groceries",
    "Fruits & Vegetables",
    "Petrol + Fastag",
    "Loan EMI / Installment",
    "Non-Veg / Protein",
    "Clothing & Personal Care",
    "Entertainment / Dining Out",
    "Education & Courses",
    "Investments / SIP",
    "Gifts & Occasions",
    "Household Services",
    "Telecom & Internet",
    "Transportation",
    "Rental Income",
    "Additional Income",
    "Miscellaneous / Other",
]

# Type mapping - income and investments are excluded from expense totals
CATEGORY_TYPE = {
    "Rental Income": "income",
    "Additional Income": "income",
    "Investments / SIP": "investment",
}
DEFAULT_TYPE = "expense"

def entry_type(category: str) -> str:
    return CATEGORY_TYPE.get(category, DEFAULT_TYPE)

# Sheet column layout (Column C to Column H)
# Col A is blank, Col B is auto formula number
COL_DATE = "C"
COL_DESCRIPTION = "D"
COL_CATEGORY = "E"
COL_AMOUNT = "F"
COL_PAID_BY = "G"
COL_COMMENT = "H"

HEADER_ROW = 6
FIRST_DATA_ROW = 8

MONTH_TAB_PREFIX = "📋 "
MONTH_TAB_SUFFIX = " Expenses"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTH_FULL_NAMES = {
    "Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April",
    "May": "May", "Jun": "June", "Jul": "July", "Aug": "August",
    "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December",
}

def month_tab_name(month_abbr: str) -> str:
    return f"{MONTH_TAB_PREFIX}{month_abbr}{MONTH_TAB_SUFFIX}"

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
QUOTA_RESET_MESSAGE_IST = (
    "Hit today's free AI quota limit for the bot. "
    "It resets around 1:30 PM IST (midnight Pacific Time) — try again after that."
)
