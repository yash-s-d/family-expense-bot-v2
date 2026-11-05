import os
from config import (
    month_tab_name, FIRST_DATA_ROW, COL_DATE, COL_DESCRIPTION,
    COL_CATEGORY, COL_AMOUNT, COL_PAID_BY, COL_COMMENT
)

class SheetsQuotaExceededError(Exception):
    pass

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

class SheetsClient:
    def __init__(self):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as e:
            raise ImportError("Please install gspread and google-auth: pip install gspread google-auth") from e

        self.gspread = gspread
        key_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
        json_raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        sheet_id = os.getenv("GOOGLE_SHEET_ID")

        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID environment variable is not set.")

        if json_raw:
            import json
            info = json.loads(json_raw)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        elif key_path and os.path.exists(key_path):
            creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
        else:
            try:
                import google.auth
                creds, _ = google.auth.default(scopes=SCOPES)
            except Exception as e:
                raise FileNotFoundError(
                    f"Google service account key not found at {key_path}, "
                    f"GOOGLE_SERVICE_ACCOUNT_JSON is not set, and ADC fallback failed: {e}"
                )

        gc = self.gspread.authorize(creds)
        self.spreadsheet = gc.open_by_key(sheet_id)

    def _get_worksheet(self, month_abbr: str):
        target_tab = month_tab_name(month_abbr)
        try:
            return self.spreadsheet.worksheet(target_tab)
        except self.gspread.WorksheetNotFound:
            # Fallback: check if tab exists without prefix/suffix (e.g. "Nov" or "November")
            worksheets = self.spreadsheet.worksheets()
            for ws in worksheets:
                if month_abbr.lower() in ws.title.lower():
                    return ws
            # If still not found, raise with clear instructions
            titles = [ws.title for ws in worksheets]
            raise ValueError(
                f"Worksheet '{target_tab}' not found. Available tabs in your sheet: {titles}. "
                f"Please ensure a tab named '{target_tab}' exists."
            )

    def _first_blank_row(self, worksheet):
        # Column D (Description) indicates whether a row is populated
        desc_col_idx = ord(COL_DESCRIPTION) - ord("A") + 1
        col_values = worksheet.col_values(desc_col_idx)
        return max(FIRST_DATA_ROW, len(col_values) + 1)

    def append_row(self, month_abbr: str, date: str, description: str,
                   category: str, amount: float, paid_by: str, comment: str = "") -> int:
        worksheet = self._get_worksheet(month_abbr)
        row_number = self._first_blank_row(worksheet)

        # Single batched update from COL_DATE to COL_COMMENT (C{row}:H{row})
        row_values = [date, description, category, amount, paid_by, comment]
        cell_range = f"{COL_DATE}{row_number}:{COL_COMMENT}{row_number}"
        try:
            worksheet.update(cell_range, [row_values])
        except self.gspread.exceptions.APIError as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                raise SheetsQuotaExceededError from e
            raise

        return row_number

    def get_month_rows(self, month_abbr: str) -> list[dict]:
        worksheet = self._get_worksheet(month_abbr)
        cell_range = f"{COL_DATE}{FIRST_DATA_ROW}:{COL_COMMENT}1000"
        try:
            all_rows = worksheet.get(cell_range, value_render_option="UNFORMATTED_VALUE")
        except self.gspread.exceptions.APIError as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                raise SheetsQuotaExceededError from e
            raise

        records = []
        for row in all_rows:
            # Pad row if some trailing cells are empty
            row = row + [""] * (6 - len(row))
            date, description, category, amount, paid_by, comment = row[:6]
            if not description:
                continue
            records.append({
                "date": date,
                "description": description,
                "category": category,
                "amount": float(amount or 0),
                "paid_by": paid_by,
                "comment": comment,
            })
        return records
