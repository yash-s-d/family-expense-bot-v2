"""
Updates Oct Overview, Nov Overview, and Dec Overview sheets in Google Sheets
with the exact Member-Wise Spending Breakdown settings, formulas, and formatting
matching the provided reference specification.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.path.append(os.path.dirname(__file__))

from sheets_client import SheetsClient

def apply_member_settings():
    sc = SheetsClient()
    worksheets = sc.spreadsheet.worksheets()
    
    # Target overview sheets
    targets = [
        {"month": "Oct", "ws": next(w for w in worksheets if "Oct Overview" in w.title), "exp_tab": "📋 Oct Expenses"},
        {"month": "Nov", "ws": next(w for w in worksheets if "Nov Overview" in w.title), "exp_tab": "📋 Nov Expenses"},
        {"month": "Dec", "ws": next(w for w in worksheets if "Dec Overview" in w.title), "exp_tab": "📋 Dec Expenses"},
    ]
    
    sep_ws = next(w for w in worksheets if "Sep Overview" in w.title)
    sep_sheet_id = sep_ws.id

    for target in targets:
        m = target["month"]
        ws = target["ws"]
        exp_tab = target["exp_tab"]
        sheet_id = ws.id
        print(f"\nUpdating {m} Overview (Sheet ID: {sheet_id})...")

        # 1. Update Headers at Row 31 (Cols B to K)
        headers = [
            "#",
            "Family Member",
            "Total Spent (₹)",
            "% of Household Spend",
            "Top Category",
            "Extra From Previous Month",
            "Income",
            "Income + Previous Month",
            "Investment",
            "Household expense cash available"
        ]
        ws.update("B31:K31", [headers])

        # 2. Update Member rows (Rows 32 to 35)
        # Row 32: Tanmay
        row_tanmay = [
            1,
            "Tanmay",
            f'=IFERROR(SUMIF(\'{exp_tab}\'!G:G,"Tanmay",\'{exp_tab}\'!F:F),0)',
            '=IFERROR(D32/$D$36,0)',
            f'=ARRAY_CONSTRAIN(ARRAYFORMULA(IFERROR(INDEX(\'{exp_tab}\'!E:E,MATCH(maxifs(\'{exp_tab}\'!F:F,\'{exp_tab}\'!G:G,"Tanmay"),\'{exp_tab}\'!F:F,0)),"N/A")), 1, 1)',
            2300,
            0,
            '=H32+G32',
            '',
            ''
        ]

        # Row 33: Mom
        row_mom = [
            2,
            "Mom",
            f'=IFERROR(SUMIF(\'{exp_tab}\'!G:G,"Mom",\'{exp_tab}\'!F:F),0)',
            '=IFERROR(D33/$D$36,0)',
            f'=ARRAY_CONSTRAIN(ARRAYFORMULA(IFERROR(INDEX(\'{exp_tab}\'!E:E,MATCH(maxifs(\'{exp_tab}\'!F:F,\'{exp_tab}\'!G:G,"Mom"),\'{exp_tab}\'!F:F,0)),"N/A")), 1, 1)',
            '=29000+12000',
            '=65000+29000-9500',
            '=H33+G33',
            '=J23',
            '=I33-J33'
        ]

        # Row 34: Dad
        row_dad = [
            3,
            "Dad",
            f'=IFERROR(SUMIFS(\'{exp_tab}\'!F:F,\'{exp_tab}\'!G:G,"Dad",\'{exp_tab}\'!E:E,"<>Additional Income"),0)',
            '=IFERROR(D34/$D$36,0)',
            f'=ARRAY_CONSTRAIN(ARRAYFORMULA(IFERROR(INDEX(\'{exp_tab}\'!E:E,MATCH(maxifs(\'{exp_tab}\'!F:F,\'{exp_tab}\'!G:G,"Dad"),\'{exp_tab}\'!F:F,0)),"N/A")), 1, 1)',
            130000,
            100000,
            '=H34+G34',
            '=I23',
            '=I34-J34'
        ]

        # Row 35: Akshat
        row_akshat = [
            4,
            "Akshat",
            f'=IFERROR(SUMIF(\'{exp_tab}\'!G:G,"Akshat",\'{exp_tab}\'!F:F),0)',
            '=IFERROR(D35/$D$36,0)',
            f'=ARRAY_CONSTRAIN(ARRAYFORMULA(IFERROR(INDEX(\'{exp_tab}\'!E:E,MATCH(maxifs(\'{exp_tab}\'!F:F,\'{exp_tab}\'!G:G,"Akshat"),\'{exp_tab}\'!F:F,0)),"N/A")), 1, 1)',
            550,
            0,
            '=H35+G35',
            0,
            '=D35-J35'
        ]

        # Row 36: Total Row
        row_totals = [
            '',
            'Total Spent',
            '=SUM(D32:D35)',
            '',
            'Total',
            '=SUM(G32:G35)',
            '=SUM(H32:H35)',
            '=SUM(I32:I35)',
            '=SUM(J32:J35)',
            '=SUM(K33:K35)'
        ]

        # Row 37: Saving
        row_saving = ['', 'Saving', '=I36-D36']

        # Row 38: Saving %
        row_saving_pct = ['', 'Saving %', '=IFERROR(D37/I36,0)']

        # Row 39: Investment %
        row_invest_pct = ['', 'Investment % ', '=IFERROR(J36/I36,0)']

        data_rows = [
            row_tanmay,
            row_mom,
            row_dad,
            row_akshat,
            row_totals,
            row_saving,
            row_saving_pct,
            row_invest_pct
        ]

        ws.update("B32:K39", data_rows, raw=False)
        print(f"Data rows updated in {m} Overview (B32:K39)")

        # 3. Copy formatting from Sep Overview to target sheet
        # Sep source range: B31:K40 (rows 31 to 40, 0-based: 30 to 40)
        # Destination range: B30:K39 (rows 30 to 39, 0-based: 29 to 39)
        batch_request = {
            "requests": [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": sep_sheet_id,
                            "startRowIndex": 30,  # Row 31 (MEMBER-WISE header)
                            "endRowIndex": 41,    # Up to row 41
                            "startColumnIndex": 1,  # Col B
                            "endColumnIndex": 11   # Col K
                        },
                        "destination": {
                            "sheetId": sheet_id,
                            "startRowIndex": 29,  # Row 30 (MEMBER-WISE header)
                            "endRowIndex": 40,    # Up to row 40
                            "startColumnIndex": 1,
                            "endColumnIndex": 11
                        },
                        "pasteType": "PASTE_FORMAT"
                    }
                }
            ]
        }
        
        try:
            sc.spreadsheet.batch_update(batch_request)
            print(f"Applied formatting from Sep Overview to {m} Overview successfully!")
        except Exception as e:
            print(f"Formatting warning for {m}: {e}")

if __name__ == "__main__":
    apply_member_settings()
