"""
Core orchestrator for Family Expense Bot.
Handles incoming messages, invokes parser, appends to sheet, and formats responses.
Also supports interactive terminal testing (`python main.py`).
"""
import os
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import (
    MONTH_NAMES, MONTH_FULL_NAMES, QUOTA_RESET_MESSAGE_IST,
    normalize_person, PEOPLE
)
from parser import MockParser, QuotaExceededError, ModelUnavailableError
from sheets_client import SheetsQuotaExceededError
from mock_sheet import MockSheetClient
from summary import compute_summary, previous_month_abbr

USE_MOCK = os.getenv("USE_MOCK", "false").lower() in ("true", "1", "yes")

_parser = None
_sheet = None
_sheet_err = None

def get_parser():
    global _parser
    if _parser is not None:
        return _parser
    if USE_MOCK:
        _parser = MockParser()
        return _parser
    if os.getenv("GEMINI_API_KEY"):
        try:
            from parser import GeminiParser
            _parser = GeminiParser()
            print("[Init] GeminiParser initialized successfully.")
            return _parser
        except Exception as e:
            print(f"[Init Warning] Failed to initialize GeminiParser: {e}. Falling back to MockParser.")
            _parser = MockParser()
            return _parser
    else:
        print("[Init] GEMINI_API_KEY not set. Using MockParser.")
        _parser = MockParser()
        return _parser

def get_sheet():
    global _sheet, _sheet_err
    if _sheet is not None:
        return _sheet, None
    if USE_MOCK:
        _sheet = MockSheetClient()
        return _sheet, None
    try:
        from sheets_client import SheetsClient
        _sheet = SheetsClient()
        _sheet_err = None
        print("[Init] SheetsClient connected to Google Sheets successfully.")
        return _sheet, None
    except Exception as e:
        _sheet_err = str(e)
        print(f"[Init Error] Failed to connect to Google Sheets: {e}")
        return None, _sheet_err

# Initialize on module load
parser = get_parser()
sheet, _init_err = get_sheet()

def current_month_abbr() -> str:
    return MONTH_NAMES[datetime.now().month - 1]

def handle_message(message: str, person: str) -> str:
    """Processes an incoming text message and returns the reply string."""
    text = message.strip()
    lowered = text.lower()

    # Handle monthly summary inquiries
    if lowered in ("summary", "how much did we spend", "monthly summary", "how much this month", "expense summary"):
        return handle_summary_request()

    active_parser = get_parser()
    try:
        entries = active_parser.parse(text)
    except QuotaExceededError:
        return QUOTA_RESET_MESSAGE_IST
    except ModelUnavailableError as e:
        print(f"\n⚠️ {e}\n")
        return "Bot is temporarily down for an AI model update — please try again in a bit."
    except Exception as e:
        print(f"Parser error: {e}")
        return "Sorry, had trouble processing that message. Try again like '250 auto' or 'eggs 60'."

    if not entries:
        return "Couldn't find an expense amount in that. Please include a number, e.g. '250 auto' or 'eggs 60'."

    active_sheet, sheet_err = get_sheet()
    if active_sheet is None:
        return f"❌ Google Sheet write failed: Could not connect to Sheet ({sheet_err})."

    month_abbr = current_month_abbr()
    today_str = datetime.now().strftime("%d-%b-%Y")
    logged = []

    for e in entries:
        try:
            row_num = active_sheet.append_row(
                month_abbr=month_abbr,
                date=today_str,
                description=e["description"],
                category=e["category"],
                amount=e["amount"],
                paid_by=person,
            )
            logged.append((row_num, e))
        except SheetsQuotaExceededError:
            return "Google Sheets is temporarily rate-limited. Please retry in a few moments."
        except Exception as e:
            print(f"Sheets write error: {e}")
            return f"Parsed ₹{e['amount']:.0f} for '{e['description']}' ({e['category']}), but failed writing to Sheet: {e}"

    if len(logged) == 1:
        row_num, e = logged[0]
        return f"✅ Logged ₹{e['amount']:,.0f} for *{e['description']}* under *{e['category']}* for *{person}* (row {row_num})."
    
    details = "\n".join([f"• ₹{e['amount']:,.0f} for {e['description']} ({e['category']})" for _, e in logged])
    return f"✅ Logged {len(logged)} entries for *{person}*:\n{details}"

def handle_summary_request() -> str:
    month_abbr = current_month_abbr()
    month_label = MONTH_FULL_NAMES[month_abbr]
    active_sheet, sheet_err = get_sheet()
    if active_sheet is None:
        return f"❌ Google Sheet error: Could not connect to Sheet ({sheet_err})."
    try:
        rows = active_sheet.get_month_rows(month_abbr)
        prev_rows = active_sheet.get_month_rows(previous_month_abbr(month_abbr))
    except SheetsQuotaExceededError:
        return "Google Sheets is briefly rate-limited — please try again in a minute."
    except Exception as e:
        return f"Could not fetch summary: {e}"
    return compute_summary(rows, prev_rows, month_label)

if __name__ == "__main__":
    mode_str = "MOCK mode" if isinstance(sheet, MockSheetClient) else "LIVE mode (Gemini + Google Sheets)"
    print("=" * 60)
    print(f" Family Expense Bot CLI Tester — {mode_str}")
    print("=" * 60)
    print("Type expense messages as if you were sending them via WhatsApp.")
    print(f"Family members: {', '.join(PEOPLE)}")
    print("Commands: 'summary', 'quit'\n")

    current_person = "Tanmay"
    while True:
        try:
            prompt_input = input(f"[{current_person}] Enter message (or switch person by typing 'as <name>'): ").strip()
            if not prompt_input:
                continue
            if prompt_input.lower() in ("quit", "exit"):
                break
            if prompt_input.lower().startswith("as "):
                new_person = normalize_person(prompt_input[3:])
                current_person = new_person
                print(f"Switched sender to: {current_person}\n")
                continue

            reply = handle_message(prompt_input, current_person)
            print(f"Bot reply:\n{reply}\n")

            if isinstance(sheet, MockSheetClient) and prompt_input.lower() not in ("summary", "how much did we spend"):
                sheet.pretty_print(current_month_abbr())
                print()
        except (KeyboardInterrupt, EOFError):
            break
