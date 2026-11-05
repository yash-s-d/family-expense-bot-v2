"""
In-memory mock Google Sheet client for offline testing.
Mirrors the exact methods of SheetsClient.
"""
from collections import defaultdict
from config import month_tab_name, FIRST_DATA_ROW

class MockSheetClient:
    def __init__(self):
        self.tabs = defaultdict(list)

    def append_row(self, month_abbr: str, date: str, description: str,
                   category: str, amount: float, paid_by: str, comment: str = "") -> int:
        tab = month_tab_name(month_abbr)
        row_number = FIRST_DATA_ROW + len(self.tabs[tab])
        self.tabs[tab].append({
            "date": date,
            "description": description,
            "category": category,
            "amount": amount,
            "paid_by": paid_by,
            "comment": comment,
        })
        return row_number

    def get_month_rows(self, month_abbr: str) -> list[dict]:
        return list(self.tabs[month_tab_name(month_abbr)])

    def pretty_print(self, month_abbr: str):
        tab = month_tab_name(month_abbr)
        rows = self.tabs[tab]
        if not rows:
            print(f"[{tab}] — no entries yet")
            return
        print(f"\n[{tab}]")
        print(f"{'#':<3} {'Date':<12} {'Description':<25} {'Category':<25} {'Amount':>10} {'Paid By':<8}")
        print("-" * 88)
        for i, r in enumerate(rows, 1):
            print(f"{i:<3} {r['date']:<12} {r['description'][:24]:<25} {r['category'][:24]:<25} "
                  f"₹{r['amount']:>8,.0f} {r['paid_by']:<8}")
