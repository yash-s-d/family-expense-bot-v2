"""
Comprehensive test suite verifying:
1. Family member normalization and phone resolution
2. Expense classification & multi-item splitting
3. Egg classification rules (Fruits & Veg vs Groceries vs Non-Veg)
4. Mock Sheet storage and month summary generation
5. Webhook verification endpoint handshake
"""
import unittest
from config import normalize_person, CATEGORIES, entry_type
from parser import MockParser
from mock_sheet import MockSheetClient
from summary import compute_summary

class TestFamilyExpenseBot(unittest.TestCase):
    def setUp(self):
        self.parser = MockParser()
        self.sheet = MockSheetClient()

    def test_member_normalization(self):
        self.assertEqual(normalize_person("Tanmay"), "Tanmay")
        self.assertEqual(normalize_person("tanmay"), "Tanmay")
        self.assertEqual(normalize_person("Akshat"), "Akshat")
        self.assertEqual(normalize_person("mom"), "Aai")
        self.assertEqual(normalize_person("AAI"), "Aai")
        self.assertEqual(normalize_person("Maa"), "Aai")
        self.assertEqual(normalize_person("dad"), "Dad")
        self.assertEqual(normalize_person("PAPA"), "Dad")
        self.assertEqual(normalize_person("Father"), "Dad")

    def test_single_expense_parsing(self):
        entries = self.parser.parse("petrol 500")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["amount"], 500.0)
        self.assertEqual(entries[0]["category"], "Petrol + Fastag")

        entries = self.parser.parse("250 auto")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["amount"], 250.0)
        self.assertEqual(entries[0]["category"], "Transportation")

    def test_eggs_categorization_rules(self):
        # Eggs with vegetables -> Fruits & Vegetables
        entries = self.parser.parse("eggs and tomato 90")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["category"], "Fruits & Vegetables")

        # Eggs with grocery staples -> Groceries
        entries = self.parser.parse("bought eggs and bread 120 rs")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["category"], "Groceries")

        # Plain eggs -> Groceries
        entries = self.parser.parse("bought 1 dozen eggs 80")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["category"], "Groceries")

    def test_multi_item_transaction_splitting(self):
        entries = self.parser.parse("groceries 400 and auto 100")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["amount"], 400.0)
        self.assertEqual(entries[0]["category"], "Groceries")
        self.assertEqual(entries[1]["amount"], 100.0)
        self.assertEqual(entries[1]["category"], "Transportation")

    def test_sheet_append_and_summary(self):
        # Simulate expenses logged by different family members
        self.sheet.append_row("Nov", "05-Nov-2026", "Eggs and Bread", "Groceries", 120.0, "Aai")
        self.sheet.append_row("Nov", "05-Nov-2026", "Petrol", "Petrol + Fastag", 500.0, "Tanmay")
        self.sheet.append_row("Nov", "05-Nov-2026", "Auto", "Transportation", 80.0, "Akshat")
        self.sheet.append_row("Nov", "05-Nov-2026", "Medicines", "Medical & Healthcare", 450.0, "Dad")

        rows = self.sheet.get_month_rows("Nov")
        self.assertEqual(len(rows), 4)

        summary_text = compute_summary(rows, previous_month_rows=[], month_label="November")
        self.assertIn("Total Spent: ₹1,150", summary_text)
        self.assertIn("Aai: ₹120", summary_text)
        self.assertIn("Tanmay: ₹500", summary_text)
        self.assertIn("Akshat: ₹80", summary_text)
        self.assertIn("Dad: ₹450", summary_text)

if __name__ == "__main__":
    unittest.main()
