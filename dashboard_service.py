"""
Dashboard Service for Family Expense Bot.
Fetches, aggregates, caches, and calculates all metrics for the Neo-Fintech Dashboard.
Directly interfaces with Google Sheets via SheetsClient with intelligent in-memory caching
and offline/mock resilience.
"""

import os
import time
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Ensure environment is loaded
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from config import (
    PEOPLE, CATEGORIES, entry_type, month_tab_name,
    MONTH_NAMES, MONTH_FULL_NAMES
)

# In-memory cache to prevent hitting Google Sheets rate limits
_CACHE: Dict[str, Any] = {}
CACHE_TTL = 90  # seconds

# Default fallback Income and Fixed data from the sheet
DEFAULT_INCOME_DATA = {
    "total_income": 185000.0,
    "sources": [
        {"name": "Papa Salary", "member": "Dad", "amount": 90000.0, "type": "Active", "pct": 48.6},
        {"name": "Aai Salary", "member": "Mom", "amount": 66000.0, "type": "Active", "pct": 35.7},
        {"name": "Rental Income", "member": "Family", "amount": 29000.0, "type": "Passive", "pct": 15.7},
    ],
    "total_fixed": 77740.0,
    "fixed_items": [
        {"name": "Aai SIP (Mutual Fund)", "category": "Investment / SIP", "member": "Mom", "amount": 30000.0, "priority": "High"},
        {"name": "Slavia Car Installment", "category": "Loan EMI", "member": "Dad", "amount": 13000.0, "priority": "Critical"},
        {"name": "Papa SIP (Mutual Fund)", "category": "Investment / SIP", "member": "Dad", "amount": 9000.0, "priority": "High"},
        {"name": "Electricity Bill", "category": "Utilities", "member": "Dad", "amount": 8000.0, "priority": "Critical"},
        {"name": "Chaitali Salary", "category": "Household Help", "member": "Mom", "amount": 5000.0, "priority": "High"},
        {"name": "Rinku Salary", "category": "Household Help", "member": "Mom", "amount": 4000.0, "priority": "High"},
        {"name": "Akshat SIP", "category": "Investment / SIP", "member": "Mom", "amount": 3000.0, "priority": "High"},
        {"name": "Milk (Monthly)", "category": "Groceries", "member": "Mom", "amount": 2100.0, "priority": "High"},
        {"name": "Wifi Bill (Airtel)", "category": "Telecom & Internet", "member": "Dad", "amount": 1340.0, "priority": "Critical"},
        {"name": "Jio Mobile Bill", "category": "Telecom & Internet", "member": "Dad", "amount": 1000.0, "priority": "Critical"},
        {"name": "Watchman / Car Wash", "category": "Household Services", "member": "Dad", "amount": 700.0, "priority": "Medium"},
        {"name": "Mahanagar Gas Bill", "category": "Utilities", "member": "Dad", "amount": 600.0, "priority": "Critical"},
    ],
    "total_annual_commitments": 177762.0,
    "total_monthly_provision": 14814.0,
    "annual_commitments": [
        {"id": 1, "name": "Health Insurance (Family)", "category": "Insurance", "responsible": "Mom", "annual_amount": 45000.0, "payment_month": "January", "monthly_provision": 3750.0, "notes": "Star Health"},
        {"id": 2, "name": "Car Insurance (Slavia)", "category": "Insurance", "responsible": "Dad", "annual_amount": 15000.0, "payment_month": "June", "monthly_provision": 1250.0, "notes": "Vehicle Insurance"},
        {"id": 3, "name": "Tanmay LIC", "category": "Insurance", "responsible": "Mom", "annual_amount": 15152.0, "payment_month": "April", "monthly_provision": 1263.0, "notes": "Life Insurance"},
        {"id": 4, "name": "Mom Money Bank", "category": "Insurance", "responsible": "Mom", "annual_amount": 10000.0, "payment_month": "Any", "monthly_provision": 833.0, "notes": "Flexible Policy"},
        {"id": 5, "name": "Mom Jeevan Anand", "category": "Insurance", "responsible": "Mom", "annual_amount": 41610.0, "payment_month": "September", "monthly_provision": 3468.0, "notes": "LIC Policy"},
        {"id": 6, "name": "Papa LIC", "category": "Insurance", "responsible": "Dad", "annual_amount": 51000.0, "payment_month": "January", "monthly_provision": 4250.0, "notes": "Life Insurance"},
    ],
    "total_loan": 29500.0,
    "financial_thermometer_pct": 15.95,
    "financial_thermometer_status": "Safe Zone: Excellent financial health. You completely own your cash flow.",
    "financial_thermometer_zone": "safe",
    "max_safe_new_emi": 7500.0,
    "loan_emis": [
        {"id": 1, "description": "Car EMI", "member": "Dad", "amount_per_month": 13000.0, "start_date": "Oct 2023", "end_date": "Sep-2030", "remaining_months": "45 Months", "notes": "Vehicle Loan"},
        {"id": 2, "description": "TV EMI", "member": "Dad", "amount_per_month": 6500.0, "start_date": "Aug 2025", "end_date": "Dec-2026", "remaining_months": "0 Months", "notes": "Consumer Durable"},
        {"id": 3, "description": "Laptop EMI", "member": "Mom", "amount_per_month": 10000.0, "start_date": "Aug 2026", "end_date": "31-Jan-2027", "remaining_months": "2 Months", "notes": "Work Laptop"}
    ]
}

def normalize_date_value(raw_val: Any) -> str:
    """Handles Excel serial dates (e.g. 46084) or string dates."""
    if isinstance(raw_val, (int, float)):
        try:
            # Excel base date is 1899-12-30
            dt = datetime(1899, 12, 30) + timedelta(days=float(raw_val))
            return dt.strftime("%d-%b-%Y")
        except Exception:
            return str(raw_val)
    if isinstance(raw_val, str):
        # Already formatted
        return raw_val.strip()
    return ""

class DashboardService:
    def __init__(self):
        self._sheets_client = None
        self._init_sheets_client()

    def _init_sheets_client(self):
        try:
            from sheets_client import SheetsClient
            self._sheets_client = SheetsClient()
        except Exception as e:
            print(f"[DashboardService] SheetsClient initialization warning: {e}")
            self._sheets_client = None

    def invalidate_cache(self, month_abbr: Optional[str] = None):
        if month_abbr:
            _CACHE.pop(f"rows_{month_abbr}", None)
            _CACHE.pop(f"summary_{month_abbr}", None)
            _CACHE.pop(f"overview_breakdown_{month_abbr}", None)
            _CACHE.pop(f"overview_cat_budgets_{month_abbr}", None)
        else:
            _CACHE.clear()

    def get_month_rows(self, month_abbr: str) -> List[Dict[str, Any]]:
        cache_key = f"rows_{month_abbr}"
        now = time.time()

        if cache_key in _CACHE:
            entry = _CACHE[cache_key]
            if now - entry["timestamp"] < CACHE_TTL:
                return entry["data"]

        rows = []
        if self._sheets_client:
            try:
                raw_rows = self._sheets_client.get_month_rows(month_abbr)
                for r in raw_rows:
                    cleaned_date = normalize_date_value(r.get("date", ""))
                    amount = float(r.get("amount") or 0)
                    rows.append({
                        "date": cleaned_date,
                        "description": str(r.get("description", "")),
                        "category": str(r.get("category", "")),
                        "amount": amount,
                        "paid_by": str(r.get("paid_by", "Unknown")),
                        "comment": str(r.get("comment", "")),
                        "type": entry_type(str(r.get("category", "")))
                    })
            except Exception as e:
                print(f"[DashboardService] Could not fetch live rows for {month_abbr}: {e}")
                # Fallback to cached data if existed, or empty
                if cache_key in _CACHE:
                    return _CACHE[cache_key]["data"]

        _CACHE[cache_key] = {"data": rows, "timestamp": now}
        return rows

    def get_income_and_fixed(self) -> Dict[str, Any]:
        """Returns the income sources and fixed monthly commitments."""
        cache_key = "income_fixed"
        now = time.time()
        if cache_key in _CACHE:
            entry = _CACHE[cache_key]
            if now - entry["timestamp"] < CACHE_TTL * 5:
                return entry["data"]

        # Default fallback (deep copy to avoid mutation)
        import copy
        data = copy.deepcopy(DEFAULT_INCOME_DATA)

        # Optionally attempt to read from '📊 Income & Fixed' sheet if connected
        if self._sheets_client:
            try:
                worksheets = self._sheets_client.spreadsheet.worksheets()
                fixed_ws = next((w for w in worksheets if "Income & Fixed" in w.title), None)
                if fixed_ws:
                    vals = fixed_ws.get_all_values()
                    annual_idx = None
                    for i, r in enumerate(vals):
                        if any("ANNUAL & ONE-TIME" in str(c).upper() for c in r):
                            annual_idx = i
                            break
                    if annual_idx is not None:
                        def parse_num(v: Any) -> float:
                            if not v or v == "-":
                                return 0.0
                            cleaned = re.sub(r"[^\d.-]", "", str(v))
                            try:
                                return float(cleaned)
                            except Exception:
                                return 0.0

                        annual_items = []
                        tot_annual = 0.0
                        tot_prov = 0.0
                        for r in vals[annual_idx + 2:]:
                            if not r or not any(r):
                                continue
                            if any("TOTAL" in str(c).upper() for c in r[:3]):
                                tot_annual = parse_num(r[5]) if len(r) > 5 else tot_annual
                                tot_prov = parse_num(r[7]) if len(r) > 7 else tot_prov
                                break
                            if len(r) >= 7 and r[2].strip():
                                a_amt = parse_num(r[5]) if len(r) > 5 else 0.0
                                p_amt = parse_num(r[7]) if len(r) > 7 else 0.0
                                annual_items.append({
                                    "id": int(r[1]) if r[1].strip().isdigit() else len(annual_items) + 1,
                                    "name": r[2].strip(),
                                    "category": r[3].strip() or "Insurance",
                                    "responsible": r[4].strip() or "Mom",
                                    "annual_amount": a_amt,
                                    "payment_month": r[6].strip(),
                                    "monthly_provision": p_amt,
                                    "notes": r[8].strip() if len(r) > 8 else ""
                                })
                        if annual_items:
                            data["annual_commitments"] = annual_items
                            data["total_annual_commitments"] = tot_annual or sum(x["annual_amount"] for x in annual_items)
                            data["total_monthly_provision"] = tot_prov or sum(x["monthly_provision"] for x in annual_items)

                    # Parse EMIs / Loan section
                    emi_idx = None
                    for i, r in enumerate(vals):
                        if any("EMIs / Loan" in str(c) or "EMIS / LOAN" in str(c).upper() for c in r):
                            emi_idx = i
                            break
                    if emi_idx is not None:
                        loan_items = []
                        tot_loan = 0.0
                        thermometer_pct = 15.95
                        thermometer_status = "Safe Zone: Excellent financial health. You completely own your cash flow."
                        thermometer_zone = "safe"
                        max_safe = 7500.0

                        for r in vals[emi_idx + 2:]:
                            if not r or not any(r):
                                continue
                            first_col = r[1].strip() if len(r) > 1 else ""
                            if "Total Loan" in first_col:
                                tot_loan = parse_num(r[4]) if len(r) > 4 else tot_loan
                            elif "Financial Thermometer" in first_col:
                                thermometer_pct = parse_num(r[4]) if len(r) > 4 else thermometer_pct
                                if len(r) > 5 and r[5].strip():
                                    raw_status = r[5].strip()
                                    # Strip leading emojis if any
                                    cleaned_status = re.sub(r"^[^\w]+", "", raw_status).strip()
                                    thermometer_status = cleaned_status or raw_status
                                    if "safe" in raw_status.lower():
                                        thermometer_zone = "safe"
                                    elif "warning" in raw_status.lower() or "moderate" in raw_status.lower():
                                        thermometer_zone = "warning"
                                    else:
                                        thermometer_zone = "alert"
                            elif "Max Safe New EMI" in first_col:
                                max_safe = parse_num(r[4]) if len(r) > 4 else max_safe
                                break
                            elif first_col.isdigit() and len(r) >= 5 and r[2].strip() and r[2].strip() != "-":
                                m_amt = parse_num(r[4]) if len(r) > 4 else 0.0
                                loan_items.append({
                                    "id": int(first_col),
                                    "description": r[2].strip(),
                                    "member": r[3].strip() or "Family",
                                    "amount_per_month": m_amt,
                                    "start_date": r[5].strip() if len(r) > 5 else "",
                                    "end_date": r[6].strip() if len(r) > 6 else "",
                                    "remaining_months": r[7].strip() if len(r) > 7 else "",
                                    "notes": r[8].strip() if len(r) > 8 else ""
                                })

                        if loan_items:
                            data["loan_emis"] = loan_items
                            data["total_loan"] = tot_loan or sum(x["amount_per_month"] for x in loan_items)
                            data["financial_thermometer_pct"] = thermometer_pct
                            data["financial_thermometer_status"] = thermometer_status
                            data["financial_thermometer_zone"] = thermometer_zone
                            data["max_safe_new_emi"] = max_safe
            except Exception as e:
                print(f"[DashboardService] Note: using default income & fixed data: {e}")

        _CACHE[cache_key] = {"data": data, "timestamp": now}
        return data

    def get_overview_spending_breakdown(self, month_abbr: str) -> Optional[Dict[str, Any]]:
        """
        Directly extracts the exact MEMBER-WISE SPENDING BREAKDOWN table from the
        Google Sheet Overview tab for the requested month.
        """
        cache_key = f"overview_breakdown_{month_abbr}"
        now = time.time()
        if cache_key in _CACHE:
            entry = _CACHE[cache_key]
            if now - entry["timestamp"] < CACHE_TTL:
                return entry["data"]

        if not self._sheets_client:
            self._init_sheets_client()

        if not self._sheets_client:
            return None

        try:
            worksheets = self._sheets_client.spreadsheet.worksheets()
            target_ws = next((w for w in worksheets if month_abbr.lower() in w.title.lower() and "overview" in w.title.lower()), None)
            if not target_ws:
                return None

            vals = target_ws.get_all_values()
            mw_idx = None
            for i, r in enumerate(vals):
                if any("MEMBER-WISE" in str(c) for c in r):
                    mw_idx = i
                    break

            if mw_idx is None:
                return None

            def parse_num(v: Any) -> float:
                if not v or v == "-":
                    return 0.0
                cleaned = re.sub(r"[^\d.-]", "", str(v))
                try:
                    return float(cleaned)
                except Exception:
                    return 0.0

            rows_data = []
            tot_row = None
            saving_val = 0.0
            saving_pct_val = 0.0
            invest_pct_val = 0.0

            for r in vals[mw_idx + 2 : min(len(vals), mw_idx + 14)]:
                if not r or not any(r):
                    continue
                first_few = [str(c).strip() for c in r[:4]]
                if any("Total" in c for c in first_few):
                    tot_row = r
                    continue
                if any("Saving %" in c for c in first_few):
                    saving_pct_val = parse_num(r[3] if len(r) > 3 else r[2])
                    continue
                if any("Investment %" in c for c in first_few):
                    invest_pct_val = parse_num(r[3] if len(r) > 3 else r[2])
                    continue
                if any("Saving" in c for c in first_few):
                    saving_val = parse_num(r[3] if len(r) > 3 else r[2])
                    continue

                if len(r) >= 9 and r[2].strip() in ["Tanmay", "Mom", "Dad", "Akshat", "Aai"]:
                    rows_data.append({
                        "num": r[1].strip() or str(len(rows_data) + 1),
                        "name": r[2].strip(),
                        "spent": parse_num(r[3]),
                        "pct_spend": parse_num(r[4]),
                        "top_category": r[5].strip() if len(r) > 5 else "-",
                        "extra_from_prev": parse_num(r[6]),
                        "income": parse_num(r[7]),
                        "income_plus_prev": parse_num(r[8]),
                        "investment": parse_num(r[9]) if len(r) > 9 else 0.0,
                        "cash_available": parse_num(r[10]) if len(r) > 10 else 0.0
                    })

            if tot_row:
                total_spent = parse_num(tot_row[3]) if len(tot_row) > 3 else sum(m["spent"] for m in rows_data)
                total_extra_prev = parse_num(tot_row[6]) if len(tot_row) > 6 else sum(m["extra_from_prev"] for m in rows_data)
                total_income = parse_num(tot_row[7]) if len(tot_row) > 7 else sum(m["income"] for m in rows_data)
                total_combined_income = parse_num(tot_row[8]) if len(tot_row) > 8 else (total_extra_prev + total_income)
                total_investment = parse_num(tot_row[9]) if len(tot_row) > 9 else sum(m["investment"] for m in rows_data)
                total_cash_avail = parse_num(tot_row[10]) if len(tot_row) > 10 else max(0.0, total_combined_income - total_investment)
            else:
                total_spent = sum(m["spent"] for m in rows_data)
                total_extra_prev = sum(m["extra_from_prev"] for m in rows_data)
                total_income = sum(m["income"] for m in rows_data)
                total_combined_income = total_extra_prev + total_income
                total_investment = sum(m["investment"] for m in rows_data)
                total_cash_avail = max(0.0, total_combined_income - total_investment)

            if saving_val == 0.0:
                saving_val = total_combined_income - total_spent
            if saving_pct_val == 0.0 and total_combined_income > 0:
                saving_pct_val = round((saving_val / total_combined_income) * 100, 2)
            if invest_pct_val == 0.0 and total_combined_income > 0:
                invest_pct_val = round((total_investment / total_combined_income) * 100, 2)

            res = {
                "rows": rows_data,
                "total_spent": total_spent,
                "total_extra_prev": total_extra_prev,
                "total_income": total_income,
                "total_combined_income": total_combined_income,
                "total_investment": total_investment,
                "total_cash_available": total_cash_avail,
                "saving": saving_val,
                "saving_pct": saving_pct_val,
                "investment_pct": invest_pct_val
            }
            _CACHE[cache_key] = {"data": res, "timestamp": now}
            return res
        except Exception as e:
            print(f"[DashboardService] Could not parse sheet overview table for {month_abbr}: {e}")
            return None

    def get_overview_category_budgets(self, month_abbr: str) -> Dict[str, Dict[str, Any]]:
        """
        Parses CATEGORY SPENDING ANALYSIS from the monthly Overview sheet.
        Returns mapping: category_name -> {budget, actual, variance, status}
        """
        cache_key = f"overview_cat_budgets_{month_abbr}"
        now = time.time()
        if cache_key in _CACHE:
            entry = _CACHE[cache_key]
            if now - entry["timestamp"] < CACHE_TTL:
                return entry["data"]

        if not self._sheets_client:
            self._init_sheets_client()

        budgets: Dict[str, Dict[str, Any]] = {}
        if self._sheets_client:
            try:
                worksheets = self._sheets_client.spreadsheet.worksheets()
                target_ws = next((w for w in worksheets if month_abbr.lower() in w.title.lower() and "overview" in w.title.lower()), None)
                if target_ws:
                    vals = target_ws.get_all_values()
                    cat_idx = None
                    for i, r in enumerate(vals):
                        if any("CATEGORY SPENDING ANALYSIS" in str(c) for c in r):
                            cat_idx = i
                            break
                    if cat_idx is not None:
                        def parse_num(v: Any) -> float:
                            if not v or v == "-":
                                return 0.0
                            is_neg = "(" in str(v) or "-" in str(v)
                            cleaned = re.sub(r"[^\d.]", "", str(v))
                            try:
                                val = float(cleaned)
                                return -val if is_neg and val > 0 else val
                            except Exception:
                                return 0.0

                        for r in vals[cat_idx + 2:]:
                            if not r or not any(r) or (len(r) > 1 and "TOTAL" in str(r[1]).upper()):
                                break
                            if len(r) > 2:
                                cat_name = str(r[2]).strip()
                                if cat_name and cat_name != "Investments / SIP":
                                    b_amt = abs(parse_num(r[3])) if len(r) > 3 else 0.0
                                    act_amt = abs(parse_num(r[4])) if len(r) > 4 else 0.0
                                    v_amt = parse_num(r[5]) if len(r) > 5 else 0.0
                                    st = str(r[7]).strip() if len(r) > 7 else ""
                                    budgets[cat_name] = {
                                        "budget": b_amt,
                                        "actual": act_amt,
                                        "variance": v_amt,
                                        "status": st
                                    }
            except Exception as e:
                print(f"[DashboardService] Could not parse category budgets for {month_abbr}: {e}")

        _CACHE[cache_key] = {"data": budgets, "timestamp": now}
        return budgets

    def compute_dashboard_metrics(self, month_abbr: str) -> Dict[str, Any]:
        """
        Calculates all numbers required by the Neo-Fintech reference design:
        1. Active balance / Net surplus
        2. Total income & rewards/inflow
        3. Category spending & Donut breakdown
        4. Member spending breakdown
        5. Inflow progress comparison
        6. Recent transactions
        """
        income_fixed = self.get_income_and_fixed()
        total_income = income_fixed["total_income"]
        total_fixed = income_fixed["total_fixed"]

        rows = self.get_month_rows(month_abbr)

        # Expense rows only (exclude income & investment SIP entries from variable spend)
        expense_rows = [r for r in rows if r["type"] == "expense"]
        total_variable_spent = sum(r["amount"] for r in expense_rows)

        # Total spent including fixed commitments
        total_household_spent = total_fixed + total_variable_spent

        # Net surplus / Active Balance
        surplus = total_income - total_household_spent
        savings_rate = (surplus / total_income * 100) if total_income > 0 else 0.0

        # Discretionary budget remaining
        discretionary_pool = max(0.0, total_income - total_fixed)
        discretionary_remaining = max(0.0, discretionary_pool - total_variable_spent)

        # Category spending breakdown & budget comparisons
        category_budgets = self.get_overview_category_budgets(month_abbr)
        default_budgets = {
            "Housing & Utilities": 10000.0,
            "Loan EMI / Installment": 41000.0,
            "Petrol + Fastag": 15000.0,
            "Medical & Healthcare": 5000.0,
            "Household Services": 10000.0,
            "Clothing & Personal Care": 0.0,
            "Gifts & Occasions": 5000.0,
            "Entertainment / Dining Out": 500.0,
            "Transportation": 5000.0,
            "Groceries": 5000.0,
            "Education & Courses": 2000.0,
            "Fruits & Vegetables": 2000.0,
            "Telecom & Internet": 2000.0,
            "Non-Veg / Protein": 2000.0,
            "Miscellaneous / Other": 2000.0,
        }

        cat_map: Dict[str, float] = {}
        for r in expense_rows:
            cat = r["category"] or "Miscellaneous / Other"
            cat_map[cat] = cat_map.get(cat, 0.0) + r["amount"]

        sorted_cats = sorted(cat_map.items(), key=lambda x: -x[1])
        top_categories = []
        for cat, amt in sorted_cats:
            pct = (amt / total_variable_spent * 100) if total_variable_spent > 0 else 0
            b_info = category_budgets.get(cat, {})
            b_amt = b_info.get("budget", default_budgets.get(cat, 0.0))
            v_amt = b_info.get("variance", (b_amt - amt if b_amt > 0 else 0.0))
            is_over = (amt > b_amt) if b_amt > 0 else (amt > 0)
            status = b_info.get("status") or ("Over" if is_over else "Under")

            top_categories.append({
                "category": cat,
                "amount": amt,
                "percentage": round(pct, 1),
                "budget": b_amt,
                "variance": v_amt,
                "is_over": is_over,
                "status": status
            })

        # Member spending breakdown
        member_map: Dict[str, float] = {}
        for r in expense_rows:
            p = r["paid_by"] or "Unknown"
            member_map[p] = member_map.get(p, 0.0) + r["amount"]

        members_breakdown = []
        for person in PEOPLE:
            amt = member_map.get(person, 0.0)
            pct = (amt / total_variable_spent * 100) if total_variable_spent > 0 else 0
            members_breakdown.append({
                "name": person,
                "amount": amt,
                "percentage": round(pct, 1)
            })

        # Previous month comparison for trend
        prev_month = self._get_previous_month(month_abbr)
        prev_rows = self.get_month_rows(prev_month)
        prev_expenses = [r for r in prev_rows if r["type"] == "expense"]
        prev_total = sum(r["amount"] for r in prev_expenses)

        spend_change_pct = 0.0
        if prev_total > 0:
            spend_change_pct = ((total_variable_spent - prev_total) / prev_total) * 100

        # Highlight insight
        top_cat_insight = "All spending within typical thresholds"
        if top_categories:
            top_cat = top_categories[0]
            top_cat_insight = f"{top_cat['category']} is your highest spend at {top_cat['percentage']}%"

        # Member-Wise Spending Breakdown & Cashflow Settings (matching reference image)
        # 1. Try to directly fetch live breakdown table from Google Sheet Overview tab
        live_breakdown = self.get_overview_spending_breakdown(month_abbr)

        if live_breakdown:
            member_breakdown_table_data = live_breakdown
            total_extra_prev = live_breakdown["total_extra_prev"]
            total_member_income = live_breakdown["total_income"]
            total_combined_income = live_breakdown["total_combined_income"]
            total_member_spent = live_breakdown["total_spent"]
            total_member_invest = live_breakdown["total_investment"]
            total_cash_avail = live_breakdown["total_cash_available"]
            member_saving = live_breakdown["saving"]
            member_saving_pct = live_breakdown["saving_pct"]
            member_invest_pct = live_breakdown["investment_pct"]
            surplus = member_saving
            total_income = total_combined_income
            # Household Living Spending strictly excludes investments as requested
            total_variable_spent = max(0.0, total_member_spent - total_member_invest)
        else:
            # Fallback computation matching user specifications
            member_settings_map = {
                "Tanmay": {"extra": 2300.0, "income": 0.0, "investment": 0.0},
                "Mom": {"extra": 41000.0, "income": 84500.0, "investment": 35000.0},
                "Dad": {"extra": 130000.0, "income": 100000.0, "investment": 0.0},
                "Akshat": {"extra": 550.0, "income": 0.0, "investment": 0.0},
            }

            # Calculate member top categories
            member_top_cats: Dict[str, Dict[str, float]] = {}
            for r in expense_rows:
                p = r["paid_by"] or "Unknown"
                if p not in member_top_cats:
                    member_top_cats[p] = {}
                c = r["category"] or "Miscellaneous"
                member_top_cats[p][c] = member_top_cats[p].get(c, 0.0) + r["amount"]

            # Calculate total spent per member across all rows
            all_member_map: Dict[str, float] = {}
            for r in rows:
                p = r["paid_by"] or "Unknown"
                if p.lower() in ["mom", "aai"]:
                    all_member_map["Mom"] = all_member_map.get("Mom", 0.0) + r["amount"]
                else:
                    all_member_map[p] = all_member_map.get(p, 0.0) + r["amount"]

            member_rows = []
            for idx, person in enumerate(["Tanmay", "Mom", "Dad", "Akshat"], 1):
                spent = all_member_map.get(person, 0.0)

                cats_for_member = member_top_cats.get(person, {})
                if person == "Mom" and "Aai" in member_top_cats:
                    for k, v in member_top_cats["Aai"].items():
                        cats_for_member[k] = cats_for_member.get(k, 0.0) + v

                top_cat_name = "-"
                if cats_for_member:
                    top_cat_name = sorted(cats_for_member.items(), key=lambda x: -x[1])[0][0]

                settings = member_settings_map[person]
                extra = settings["extra"]
                inc = settings["income"]
                inc_plus_prev = extra + inc
                invest = settings["investment"]
                cash_avail = max(0.0, inc_plus_prev - invest)
                if person == "Akshat" and cash_avail == 0:
                    cash_avail = spent

                member_rows.append({
                    "num": str(idx),
                    "name": person,
                    "spent": spent,
                    "pct_spend": 0.0,
                    "top_category": top_cat_name,
                    "extra_from_prev": extra,
                    "income": inc,
                    "income_plus_prev": inc_plus_prev,
                    "investment": invest,
                    "cash_available": cash_avail
                })

            total_member_spent = sum(m["spent"] for m in member_rows)
            for m in member_rows:
                m["pct_spend"] = round((m["spent"] / total_member_spent * 100), 1) if total_member_spent > 0 else 0.0

            total_extra_prev = sum(m["extra_from_prev"] for m in member_rows)
            total_member_income = sum(m["income"] for m in member_rows)
            total_combined_income = sum(m["income_plus_prev"] for m in member_rows)
            total_member_invest = sum(m["investment"] for m in member_rows)
            total_cash_avail = sum(m["cash_available"] for m in member_rows)

            member_saving = total_combined_income - total_member_spent
            member_saving_pct = (member_saving / total_combined_income * 100) if total_combined_income > 0 else 0.0
            member_invest_pct = (total_member_invest / total_combined_income * 100) if total_combined_income > 0 else 0.0
            surplus = member_saving
            total_income = total_combined_income
            # Household Living Spending strictly excludes investments as requested
            total_variable_spent = max(0.0, total_member_spent - total_member_invest)

            member_breakdown_table_data = {
                "rows": member_rows,
                "total_spent": total_member_spent,
                "total_extra_prev": total_extra_prev,
                "total_income": total_member_income,
                "total_combined_income": total_combined_income,
                "total_investment": total_member_invest,
                "total_cash_available": total_cash_avail,
                "saving": member_saving,
                "saving_pct": round(member_saving_pct, 2),
                "investment_pct": round(member_invest_pct, 2)
            }

        # Reverse rows for newest first in transactions
        recent_txs = list(reversed(rows))[:12]

        # Timeline and Reminders for Annual Commitments
        month_num_map = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        current_m_num = month_num_map.get(month_abbr.lower(), 11)

        raw_annual = income_fixed.get("annual_commitments", DEFAULT_INCOME_DATA.get("annual_commitments", []))
        processed_annual = []
        upcoming_reminders = []

        for item in raw_annual:
            pm = str(item.get("payment_month", "")).strip()
            pm_lower = pm.lower()
            if pm_lower in ["any", "flexible", "-"]:
                diff = 99
                status_text = "Flexible / Any Month"
                urgency = "flexible"
                is_upcoming = False
            else:
                due_num = month_num_map.get(pm_lower, 0)
                if due_num > 0:
                    diff = (due_num - current_m_num) % 12
                    if diff == 0:
                        status_text = "Due this month!"
                        urgency = "critical"
                        is_upcoming = True
                    elif diff == 1:
                        status_text = "1 month to go (Due Next Month!)"
                        urgency = "warning"
                        is_upcoming = True
                    elif diff == 2:
                        status_text = "2 months remaining"
                        urgency = "upcoming"
                        is_upcoming = True
                    elif diff == 3:
                        status_text = "3 months to go"
                        urgency = "upcoming"
                        is_upcoming = True
                    else:
                        status_text = f"{diff} months to go"
                        urgency = "future"
                        is_upcoming = False
                else:
                    diff = 99
                    status_text = pm
                    urgency = "neutral"
                    is_upcoming = False

            entry = dict(item)
            entry["months_remaining"] = diff
            entry["timeline_status"] = status_text
            entry["urgency"] = urgency
            entry["is_upcoming"] = is_upcoming
            processed_annual.append(entry)

            if is_upcoming:
                upcoming_reminders.append(entry)

        # Sort reminders by closest months remaining
        upcoming_reminders.sort(key=lambda x: x["months_remaining"])
        if not upcoming_reminders:
            fixed_dated = [x for x in processed_annual if x["months_remaining"] < 90]
            if fixed_dated:
                fixed_dated.sort(key=lambda x: x["months_remaining"])
                upcoming_reminders = fixed_dated[:2]

        return {
            "month": month_abbr,
            "month_full": MONTH_FULL_NAMES.get(month_abbr, month_abbr),
            "currency": "INR",
            "currency_symbol": "₹",
            "total_spent": total_member_spent,
            "saving": member_saving,
            "saving_pct": round(member_saving_pct, 2),
            "total_investment": total_member_invest,
            "investment_pct": round(member_invest_pct, 2),
            "active_balance": surplus,
            "total_income": total_combined_income,
            "income_plus_previous_month": total_combined_income,
            "current_month_income": total_member_income,
            "extra_from_previous_month": total_extra_prev,
            "total_fixed": total_fixed,
            "total_variable_spent": total_variable_spent,
            "spending_excl_investments": total_variable_spent,
            "total_household_spent": total_member_spent,
            "discretionary_pool": discretionary_pool,
            "discretionary_remaining": discretionary_remaining,
            "savings_rate": round(member_saving_pct, 1),
            "spend_change_pct": round(spend_change_pct, 1),
            "top_cat_insight": top_cat_insight,
            "categories": top_categories,
            "members": members_breakdown,
            "member_breakdown_table": member_breakdown_table_data,
            "income_sources": income_fixed["sources"],
            "fixed_commitments": income_fixed["fixed_items"],
            "annual_commitments": processed_annual,
            "total_annual_commitments": income_fixed.get("total_annual_commitments", 177762.0),
            "total_monthly_provision": income_fixed.get("total_monthly_provision", 14814.0),
            "upcoming_reminders": upcoming_reminders,
            "loan_emis": income_fixed.get("loan_emis", DEFAULT_INCOME_DATA.get("loan_emis", [])),
            "total_loan": income_fixed.get("total_loan", 29500.0),
            "financial_thermometer_pct": income_fixed.get("financial_thermometer_pct", 15.95),
            "financial_thermometer_status": income_fixed.get("financial_thermometer_status", "Safe Zone: Excellent financial health. You completely own your cash flow."),
            "financial_thermometer_zone": income_fixed.get("financial_thermometer_zone", "safe"),
            "max_safe_new_emi": income_fixed.get("max_safe_new_emi", 7500.0),
            "recent_transactions": recent_txs,
            "all_transactions_count": len(rows),
            "all_months": self.get_available_months()
        }

    def _get_previous_month(self, month_abbr: str) -> str:
        try:
            idx = MONTH_NAMES.index(month_abbr)
            return MONTH_NAMES[idx - 1]
        except Exception:
            return "Oct"

    def get_available_months(self) -> List[Dict[str, Any]]:
        return [
            {"abbr": "Nov", "name": "November 2026", "has_data": True, "active": True},
            {"abbr": "Oct", "name": "October 2026", "has_data": True, "active": False},
            {"abbr": "Sep", "name": "September 2026", "has_data": True, "active": False},
            {"abbr": "Dec", "name": "December 2026", "has_data": True, "active": False},
            {"abbr": "Mar", "name": "March 2026", "has_data": True, "active": False},
            {"abbr": "Apr", "name": "April 2026", "has_data": False, "active": False},
            {"abbr": "May", "name": "May 2026", "has_data": False, "active": False},
            {"abbr": "Jun", "name": "June 2026", "has_data": False, "active": False},
            {"abbr": "Jul", "name": "July 2026", "has_data": False, "active": False},
            {"abbr": "Aug", "name": "August 2026", "has_data": False, "active": False},
            {"abbr": "Jan", "name": "January 2026", "has_data": False, "active": False},
            {"abbr": "Feb", "name": "February 2026", "has_data": False, "active": False},
        ]

    def update_member_settings_in_sheet(self, month_abbr: str, member_updates: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Updates Extra From Previous Month and Income in the monthly overview sheet."""
        if not self._sheets_client:
            self._init_sheets_client()
        if not self._sheets_client:
            raise RuntimeError("Google Sheets client not available")

        # Find target overview sheet
        worksheets = self._sheets_client.spreadsheet.worksheets()
        target_ws = next((w for w in worksheets if f"{month_abbr} Overview" in w.title), None)
        if not target_ws:
            raise ValueError(f"Overview sheet for {month_abbr} not found")

        # Member row mapping in Overview tab (Tanmay: row 32, Mom: row 33, Dad: row 34, Akshat: row 35)
        row_map = {"Tanmay": 32, "Mom": 33, "Dad": 34, "Akshat": 35}
        for member, vals in member_updates.items():
            if member in row_map:
                r = row_map[member]
                if "extra" in vals:
                    target_ws.update(f"G{r}", [[vals["extra"]]])
                if "income" in vals:
                    target_ws.update(f"H{r}", [[vals["income"]]])
                if "investment" in vals:
                    target_ws.update(f"J{r}", [[vals["investment"]]])

        self.invalidate_cache(month_abbr)
        return {"success": True, "message": f"Updated {month_abbr} budget settings in Google Sheet"}

    def add_expense(self, month_abbr: str, date_str: str, description: str,
                    category: str, amount: float, paid_by: str, comment: str = "") -> Dict[str, Any]:
        """Appends a new expense to Google Sheet and clears cache."""
        if not self._sheets_client:
            self._init_sheets_client()

        if not self._sheets_client:
            raise RuntimeError("Google Sheets client is not connected.")

        row_num = self._sheets_client.append_row(
            month_abbr=month_abbr,
            date=date_str,
            description=description,
            category=category,
            amount=amount,
            paid_by=paid_by,
            comment=comment
        )
        self.invalidate_cache(month_abbr)
        return {
            "success": True,
            "row_number": row_num,
            "message": f"Successfully added ₹{amount:,.0f} for '{description}' paid by {paid_by}"
        }

# Singleton instance
dashboard_service = DashboardService()
