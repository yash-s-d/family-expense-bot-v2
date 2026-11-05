"""
Parses free-text WhatsApp messages into structured expense entries.
Includes:
  - GeminiParser: AI-powered extraction using Google Gemini API.
  - MockParser: Offline regex-based rule extractor for local testing without an API key.
"""
import os
import re
import json
from config import CATEGORIES, entry_type

PARSE_PROMPT_TEMPLATE = """You are parsing a short WhatsApp message from a family member logging an expense (or income/investment) into a household finance tracker.

Categories you MUST choose from (exact spelling):
{categories}

Rules:
1. If the message mentions eggs together with vegetables/fruits (e.g. "eggs and tomato", "eggs 60 spinach 40"), classify eggs as "Fruits & Vegetables".
2. If the message mentions eggs together with groceries/staples (e.g. "eggs and bread", "milk eggs 120", "kirana"), classify as "Groceries".
3. If eggs are bought alone or with non-veg (e.g. "eggs and chicken"), classify as "Non-Veg / Protein" or "Groceries".
4. If the message describes ONE shopping trip with multiple items and ONE total amount (e.g. "700 vegetables paneer milk etc"), return ONE entry — keep the item list in "description", do not split it.
5. If the message clearly describes MULTIPLE SEPARATE transactions with DIFFERENT amounts (e.g. "groceries 400 and auto 100"), return MULTIPLE entries, one per amount.
6. If you cannot confidently match a category, use "Miscellaneous / Other".
7. Amount formats to handle: "100/-", "Rs 100", "100rs", "₹100", "100 rupees", plain "100".
8. Return ONLY valid JSON, no markdown code fence, no commentary, matching this exact shape:

{{"entries": [{{"amount": <number>, "category": "<one of the categories above>", "description": "<short description>"}}]}}

If no valid amount can be found, return {{"entries": []}}.

Message: "{message}"
"""

class QuotaExceededError(Exception):
    pass

class ModelUnavailableError(Exception):
    pass

class GeminiParser:
    """Real AI parser using Google Gemini API."""

    def __init__(self, model_name: str = None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")

        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self._init_client(api_key)

    def _init_client(self, api_key: str):
        # Supports the modern google-genai SDK or fallback to google-generativeai
        try:
            from google import genai
            self.client_type = "genai"
            self.client = genai.Client(api_key=api_key)
        except ImportError:
            import google.generativeai as gai
            self.client_type = "gai"
            gai.configure(api_key=api_key)
            self.client = gai.GenerativeModel(self.model_name)

    def parse(self, message: str) -> list[dict]:
        prompt = PARSE_PROMPT_TEMPLATE.format(categories=", ".join(CATEGORIES), message=message)
        try:
            if self.client_type == "genai":
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                text = response.text
            else:
                response = self.client.generate_content(prompt)
                text = response.text
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                raise QuotaExceededError from e
            if "404" in err or "not found" in err.lower() or "no longer available" in err.lower():
                raise ModelUnavailableError(f"Model {self.model_name} unavailable: {err}") from e
            raise

        cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(cleaned)
            return data.get("entries", [])
        except json.JSONDecodeError:
            return []


class MockParser:
    """
    Rule-based mock parser for instant offline testing without API keys.
    """
    RULES = [
        (r"medical|hospital|doctor|pharmacy|clinic|medicine|tablet|syrup", "Medical & Healthcare"),
        (r"electricity|gas bill|cylinder|maintenance|rent paid", "Housing & Utilities"),
        (r"haircut|clothes|dress|shopping|salon|parlour|shirt|pants", "Clothing & Personal Care"),
        (r"movie|zomato|swiggy|dining|lunch out|dinner|pizza|burger|chai|coffee", "Entertainment / Dining Out"),
        (r"book|pencil|pen|course|college fee|exam fee|tuition|school", "Education & Courses"),
        (r"\bgift\b|birthday|anniversary", "Gifts & Occasions"),
        (r"maid|cook|ironing|dry clean|cleaner|watchman", "Household Services"),
        (r"jio|airtel|wifi|spotify|phone bill|recharge|broadband", "Telecom & Internet"),
        (r"uber|train|auto|rapido|bus|airplane|flight|ola|metro", "Transportation"),
        (r"petrol|diesel|fuel|fastag|cng|toll", "Petrol + Fastag"),
        (r"\bemi\b|loan|installment", "Loan EMI / Installment"),
        (r"sip|silver|gold|\bfd\b|\brd\b|insurance|\blic\b|mutual fund|shares|stock", "Investments / SIP"),
        (r"chicken|fish|mutton|prawns", "Non-Veg / Protein"),
        (r"rent received|rental income|rent collected", "Rental Income"),
        (r"salary|bonus|freelance|cashback|dividend", "Additional Income"),
    ]

    def parse(self, message: str) -> list[dict]:
        # First, temporarily protect quantity units like "1 dozen", "2 kg", "500 gm", "3 packets"
        # so they aren't mistaken for prices or split points
        unit_pattern = r"\b(\d+)\s*(dozen|kg|kgs|gm|gms|g|l|ltr|liter|litre|packet|packets|pkt|pkts|pc|pcs|bunch|piece|pieces|plate|plates)\b"
        cleaned_msg = re.sub(unit_pattern, r"[\1 \2]", message, flags=re.IGNORECASE)

        # Check if multiple transactions are chained with 'and' or commas (each having its own amount)
        segments = re.split(r"\band\b|,(?!\d)", cleaned_msg, flags=re.IGNORECASE)
        segments = [s.strip() for s in segments if s.strip()]

        # Find numbers not enclosed in brackets
        def has_price(s: str) -> bool:
            return bool(re.search(r"(?<!\[)\b\d+(?:\.\d{1,2})?\b(?![\s\w]*\])", s))

        if not (len(segments) > 1 and all(has_price(s) for s in segments)):
            segments = [cleaned_msg]

        entries = []
        for seg in segments:
            # Find candidate amounts (numbers not enclosed in brackets)
            matches = list(re.finditer(r"(?:rs\.?|₹)?\s*(?<!\[)\b(\d+(?:\.\d{1,2})?)\b(?![\s\w]*\])\s*(?:/-|rs|rupees)?", seg, re.IGNORECASE))
            if not matches:
                continue

            # If multiple numbers, prefer one with currency symbol or take the last number as price
            chosen = matches[-1]
            for m in matches:
                matched_str = seg[m.start():m.end()]
                if any(sym in matched_str.lower() for sym in ("rs", "₹", "/-", "rupee")):
                    chosen = m
                    break

            amount = float(chosen.group(1))

            # Strip amount out of the text to leave description
            start, end = chosen.span()
            desc = seg[:start] + seg[end:]
            # Restore bracketed units
            desc = desc.replace("[", "").replace("]", "")
            desc = re.sub(r"\b(paid|for|spent|bought|brought|got|purchased|received)\b", "", desc, flags=re.IGNORECASE).strip()
            desc = re.sub(r"\s+", " ", desc).strip() or "Expense"

            category = self._classify(seg)
            entries.append({"amount": amount, "category": category, "description": desc})

        return entries

    def _classify(self, text: str) -> str:
        for pattern, cat in self.RULES:
            if re.search(pattern, text, re.IGNORECASE):
                return cat

        # Eggs specific logic
        has_eggs = re.search(r"egg|eggs|anda|ande", text, re.IGNORECASE)
        has_veg = re.search(r"vegetable|sabzi|bhaji|paneer|tomato|onion|potato|fruit|apple|banana", text, re.IGNORECASE)
        has_grocery = re.search(r"groceries|grocery|milk|dmart|kirana|aata|flour|bread|butter|cheese|dal|rice|oil|biscuit", text, re.IGNORECASE)

        if has_eggs and has_veg:
            return "Fruits & Vegetables"
        if has_eggs and (has_grocery or not has_veg):
            return "Groceries"
        if has_veg:
            return "Fruits & Vegetables"
        if has_grocery:
            return "Groceries"

        return "Miscellaneous / Other"
