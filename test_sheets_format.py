import sys
import os
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.path.append(os.path.dirname(__file__))

from sheets_client import SheetsClient
sc = SheetsClient()

worksheets = sc.spreadsheet.worksheets()
sep_ws = next(w for w in worksheets if "Sep Overview" in w.title)
oct_ws = next(w for w in worksheets if "Oct Overview" in w.title)
nov_ws = next(w for w in worksheets if "Nov Overview" in w.title)
dec_ws = next(w for w in worksheets if "Dec Overview" in w.title)

print(f"Sep: {sep_ws.id}, Oct: {oct_ws.id}, Nov: {nov_ws.id}, Dec: {dec_ws.id}")
