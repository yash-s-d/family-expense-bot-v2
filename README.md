# WhatsApp Family Expense Bot

An automated WhatsApp bot for tracking shared family expenses across **Tanmay, Akshat, Aai, and Dad**. 

Whenever any family member texts an expense to the free Meta WhatsApp test number (e.g. *"bought eggs 60 rs"*, *"250 auto"*, or *"groceries 400 and auto 100"*), the AI categorizes the expense, automatically appends a new row to the shared Google Sheet under the current month tab, and replies with a confirmation.

---

## Features

- **Hands-Free WhatsApp Interface**: Log expenses in natural conversational Hindi/English without manual sheet entry.
- **AI-Powered Categorization**: Uses Google Gemini to extract amount, item description, and match against predefined categories.
- **Multi-Family Member Tracking**: Identifies the sender by their WhatsApp number and records who paid (**Tanmay**, **Akshat**, **Aai**, **Dad**).
- **Multi-Item Splitting**: Automatically splits messages like *"groceries 400 and auto 100"* into distinct rows.
- **Instant Confirmation**: Replies with the logged category and sheet row number.
- **Monthly Summary on Demand**: Text *"summary"* or *"how much did we spend"* to get a total expense breakdown by category and family member.
- **Quota-Safe Batched Writes**: Avoids Google Sheets rate-limiting by batching row updates.
- **Zero-Dependency CLI Test Mode**: Test locally in terminal immediately without waiting for API keys.

---

## Quick Start (Local CLI Test)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run in CLI mode
python main.py
```

---

## Complete Setup Guide

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for full instructions on:
1. Generating a free Google Gemini API key.
2. Creating a Google Cloud Service Account & sharing your Google Sheet.
3. Setting up the free WhatsApp test number on Meta Developer Portal.
4. Exposing your webhook using ngrok.
