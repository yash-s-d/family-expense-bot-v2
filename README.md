# 🇮🇳 Family Expense Bot: WhatsApp-Based Automated Household Budget Tracker

> **Turning the chaos of frictionless UPI spending into effortless, real-time family financial peace of mind.**

[![Live on Cloud Run](https://img.shields.io/badge/Hosted%20On-Google%20Cloud%20Run-blue?logo=googlecloud)](https://cloud.google.com/run)
[![AI Engine](https://img.shields.io/badge/AI%20Engine-Gemini%20Flash%20Lite-orange?logo=google)](https://aistudio.google.com/)
[![Messaging](https://img.shields.io/badge/Messaging-WhatsApp%20Cloud%20API-green?logo=whatsapp)](https://developers.facebook.com/)
[![Database](https://img.shields.io/badge/Ledger-Google%20Sheets-success?logo=googlesheets)](https://docs.google.com/spreadsheets)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 The Real Indian Household Pain Point

In India today, **UPI has made spending dangerously frictionless**. 

Every adult in a 4-to-5 member family carries a smartphone equipped with 2 to 4 UPI apps—Google Pay, PhonePe, Paytm, CRED. Whether it's buying a pack of milk for ₹30, paying the vegetable vendor ₹120, or taking an auto for ₹80, money leaves bank accounts with just a quick QR scan and a 4-digit PIN.

### The Problem: Invisible Multi-Person Spending

1. **Category Overlap & Double-Spending**:
   - Mom buys ₹300 worth of vegetables in the morning.
   - Dad, unaware, stops by the mandi in the evening and buys another ₹250 of vegetables.
   - Multiple family members spend money on the exact same categories simultaneously without anyone realizing it.
2. **The Month-End Diary & Excel Nightmare**:
   - At the end of every month, moms or family accountants face peak frustration.
   - Sitting down with a pen and notebook, scrolling through endless bank SMS notifications (*"debited by INR 45..."*), and trying to remember who bought what 3 weeks ago is exhausting and sparks unnecessary arguments.
3. **The Month-End "Expense Shock"**:
   - When the family finally checks their bank accounts, discovering that ₹40,000 or ₹70,000 vanished without a clear trace is shocking. It's a glaring symptom of broken personal finance tracking.
4. **Why Traditional Budgeting Apps Fail**:
   - Asking parents or siblings to install a complex new finance app, register an account, and fill out 5-step dropdown menus for every single cup of chai fails within 3 days.

### The Solution: Zero-Behavior-Change WhatsApp Tracker

Indian families already spend their day on **WhatsApp**. Grandparents, parents, and kids use it effortlessly. 

With this bot:
- You finish paying via UPI at the counter.
- You open WhatsApp and send a 3-second text to your family bot:
  - *"bought eggs and bread 120 rs"*
  - *"250 auto"*
  - *"doodh aur sabzi 150"*
- **Google Gemini AI** extracts the amount, understands natural Hinglish, categorizes the item, records who paid based on your phone number, and instantly appends it to your shared family **Google Sheet**.
- You receive an immediate confirmation, keeping the entire family on the same page in real time!

---

## 🔄 Visual Comparison: Before vs. After

| The Old Way (The UPI Chaos Trap) ❌ | The Family Expense Bot Way (Effortless Tracking) ✅ |
|---|---|
| Multiple family members spend via UPI silently | Everyone texts expenses in natural language on WhatsApp |
| Zero communication; frequent accidental double-spending | Live Google Sheet gives real-time visibility to everyone |
| Mom suffers through stressful month-end notebook/Excel work | Automated, instant categorization & auto-tab generation |
| End-of-month panic: *"Where did all our money go?"* | Text *"summary"* anytime for instant category breakdowns |
| Complex budgeting apps abandoned after 3 days | Uses WhatsApp—the app your family already uses daily |

---

## 📊 How It Works: Visual Architecture

### High-Level Workflow (Non-Technical View)

```mermaid
flowchart LR
    A[👤 Family Member<br/>Tanmay / Akshat / Aai / Dad] -->|Texts: 'bought eggs 60 rs'| B[💬 WhatsApp]
    B -->|Webhook| C[⚡ Google Cloud Run<br/>Serverless Engine]
    C -->|Natural Language| D[🧠 Google Gemini AI<br/>Extracts Amount & Category]
    D -->|Item: Eggs | Category: Groceries | Amount: 60| C
    C -->|Appends New Row| E[📋 Live Google Sheet<br/>Shared Family Dashboard]
    C -->|Confirmation Reply| B
    B -->|'✅ Logged ₹60 for Groceries'| A
```

### Detailed Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Family Member (e.g. Tanmay)
    participant WA as WhatsApp (Meta API)
    participant CR as Google Cloud Run (Flask Webhook)
    participant AI as Google Gemini 3.5 Flash Lite
    participant GS as Google Sheets (gspread)

    User->>WA: 'groceries 400 and auto 100'
    WA->>CR: POST /webhook (Inbound Message Payload)
    CR->>CR: Identify Sender Number -> Map to 'Tanmay'
    CR->>AI: Parse Text & Split Multi-Items
    AI-->>CR: Return JSON: [{Item: Groceries, ₹400}, {Item: Auto, ₹100, Cat: Transportation}]
    CR->>GS: Batch Append Rows to Current Month Tab
    GS-->>CR: Success (Rows 42, 43 logged)
    CR->>WA: Send Outbound WhatsApp Message
    WA-->>User: '✅ Logged 2 items:
• Groceries: ₹400
• Transportation: ₹100'
```

---

## ✨ Key Features

- **🗣️ Natural Hinglish & Conversational Parsing**: Handles messages like *"doodh 60"*, *"auto meter 140"*, *"bought 1 dozen bananas 70 rs"*, or *"paid electricity bill 1850"*.
- **✂️ Multi-Item Splitting**: Automatically splits compound messages like *"groceries 400 and auto 100"* into separate rows with distinct categories.
- **👨‍👩‍👧‍👦 Multi-Member Attribution**: Identifies the sender automatically by WhatsApp phone number (**Tanmay**, **Akshat**, **Aai**, **Dad**). Also understands third-party payments (e.g., *"Dad paid 1200 for wifi"*).
- **📋 Live Google Sheets Sync**: Writes directly to the active month's tab (e.g., `📋 Nov Expenses`), color-coding amounts and maintaining category columns.
- **⚡ Quota-Safe Batched Updates**: Prevents Google Sheets 429 rate-limiting by writing cell ranges (`C{row}:H{row}`) in atomic batches.
- **📈 On-Demand Monthly Summaries**: Text *"summary"* or *"how much did we spend"* to receive a breakdown of total expenditure by category and individual member shares.
- **☁️ 24/7 Serverless & 100% Free**: Hosted on Google Cloud Run (under Google's 2,000,000 free monthly requests) and Gemini Flash Lite (free tier), requiring zero paid subscriptions or local machines running.

---

## 🛠️ The Tech Stack (Explained Simply)

| Technology | Role | Why We Chose It |
|---|---|---|
| **WhatsApp Cloud API (Meta)** | Messaging Frontend | Zero learning curve. No apps to install for family members. Free test number included. |
| **Google Gemini 3.5 Flash Lite** | Natural Language AI | Lightning-fast JSON extraction (~400ms), understands Indian context/slang, free high rate limits. |
| **Flask (Python 3.11)** | Webhook Application | Lightweight, clean routing, easy integration with gspread and Meta Cloud API. |
| **Google Sheets API (`gspread`)** | Cloud Database / Ledger | Accessible to everyone, easy to format, exportable to Excel or PDF anytime. |
| **Google Cloud Run** | Serverless Cloud Hosting | Runs 24/7 in Mumbai (`asia-south1`), auto-sleeps when idle, completely free tier. |
| **Docker** | Containerization | Predictable, repeatable deployment across any machine or cloud platform. |

---

## 🚀 Turnkey Replication Blueprint (Step-by-Step)

Want to set up this exact system for your own family? Follow this step-by-step guide. You can complete the whole setup in under 20 minutes for **₹0 / $0**.

### Prerequisites
- A Google Account (for Sheets & Gemini API)
- A Meta Developer Account (free at [developers.facebook.com](https://developers.facebook.com/))
- A GitHub Account

---

### Step 1: Fork or Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/yash-s-d/family-expense-bot-v2.git
cd family-expense-bot-v2
```

---

### Step 2: Get a Free Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account and click **Get API key**.
3. Create a key in a new or existing Google Cloud project.
4. Copy the API key string (e.g. `AIzaSy...`).

---

### Step 3: Set Up Your Google Sheet & Service Account
1. Create a Google Sheet or copy our template.
2. In your Google Cloud Console:
   - Enable the **Google Sheets API** and **Google Drive API**.
   - Navigate to **IAM & Admin > Service Accounts** and create a service account (e.g., `sheets-writer`).
   - Click on the service account > **Keys** > **Add Key** > **Create new key (JSON)**.
   - Save the downloaded JSON file as `service_account.json` in your project root (or keep its contents ready).
3. Open your Google Sheet, click **Share**, and paste the service account email (e.g., `sheets-writer@project.iam.gserviceaccount.com`) as an **Editor**.
4. Copy the Sheet ID from the URL (`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`).

---

### Step 4: Configure WhatsApp Business Cloud API
1. Go to [Meta for Developers](https://developers.facebook.com/) and create an app:
   - Type: **Other** > **Business**.
   - App Name: `Family Expense Bot`.
2. In your App Dashboard, add the **WhatsApp** product.
3. Under **WhatsApp > API Setup**:
   - You will see a **Temporary Access Token** and a **Phone Number ID**.
   - Under *To*, add your family members' phone numbers (with country code, e.g., `919876543210`) as verified test recipients.
4. (Optional for Permanent Token): Create a System User under **Meta Business Suite > Users > System Users**, assign the WhatsApp app with `whatsapp_business_messaging` permissions, and generate a permanent token.

---

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```
Edit `.env`:
```ini
# Google Gemini AI
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# Google Sheets
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# Meta WhatsApp Cloud API
WHATSAPP_TOKEN=EAAGYourMetaWhatsAppTokenHere
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WEBHOOK_VERIFY_TOKEN=choose_any_secret_passphrase_here

# Family Phone Numbers (Country code + 10 digits without +)
TANMAY_PHONE=919082500861
AKSHAT_PHONE=919876543210
AAI_PHONE=919876543211
DAD_PHONE=919876543212
```

---

### Step 6: Test Locally (Zero Setup CLI Mode)
You can test the logic immediately without any webhooks or cloud setup:
```bash
pip install -r requirements.txt
python main.py
```
Type any expense in the console:
```text
Enter expense: 1 dozen bananas 60 rs
>> [Tanmay] Bananas -> Groceries: Rs 60
Enter expense: auto 120 and medical 350
>> [Tanmay] Auto -> Transportation: Rs 120
>> [Tanmay] Medical -> Healthcare: Rs 350
```

---

### Step 7: Deploy 24/7 Serverless to Google Cloud Run

To keep the bot running permanently without keeping your computer on:
1. Push your code to GitHub.
2. In Google Cloud Console, open **Cloud Run** and click **Deploy Container > Service from source repository**.
3. Select your GitHub repository (`family-expense-bot-v2`) and branch (`main`).
4. Select Region: `asia-south1` (Mumbai) for ultra-low latency in India.
5. In **Environment Variables**, paste the keys from your `.env` file (including `GOOGLE_SERVICE_ACCOUNT_JSON` as raw JSON string).
6. Click **Create / Deploy**.
7. Once deployed, Cloud Run gives you a live HTTPS URL:
   `https://your-service-name.run.app`

---

### Step 8: Connect Webhook in Meta Developer Portal
1. In Meta Developer Dashboard > **WhatsApp > Configuration**:
   - **Callback URL**: `https://your-service-name.run.app/webhook`
   - **Verify Token**: The same value you set for `WEBHOOK_VERIFY_TOKEN` in your `.env`.
   - Click **Verify and Save**.
2. Under **Webhook fields**, click **Manage** and subscribe to `messages`.
3. Under WhatsApp API Setup, send a message to the test phone number from WhatsApp on your phone.
4. **Done! 🎉** You will get an instant reply and the expense will appear in your Google Sheet!

---

## 📱 Example WhatsApp Interaction

```text
Tanmay:
auto 120 rs and lunch 350

Bot:
✅ Logged 2 expenses:
1. Auto: ₹120 [Transportation] (Row 42)
2. Lunch: ₹350 [Food & Dining] (Row 43)
Paid by: Tanmay

---

Aai:
sabzi 180 aur doodh 65

Bot:
✅ Logged 2 expenses:
1. Sabzi: ₹180 [Fruits & Vegetables] (Row 44)
2. Doodh: ₹65 [Groceries] (Row 45)
Paid by: Aai

---

Akshat:
summary

Bot:
📊 November 2026 Expense Summary:
Total Spent: ₹14,850

By Category:
• Groceries: ₹4,200 (28.3%)
• Food & Dining: ₹3,100 (20.9%)
• Transportation: ₹2,450 (16.5%)
• Utilities: ₹2,100 (14.1%)
• Healthcare: ₹1,800 (12.1%)
• Others: ₹1,200 (8.1%)

By Family Member:
• Tanmay: ₹5,400 (36.4%)
• Dad: ₹4,800 (32.3%)
• Aai: ₹3,150 (21.2%)
• Akshat: ₹1,500 (10.1%)
```

---

## 💻 Modern Neo-Fintech Web Dashboard (2026)

Beyond WhatsApp tracking, the bot features a **Neo-Fintech Web Dashboard** built with minimalist neobank aesthetics:

* **Overview Command Center**:
  * **Living Spend Hero**: Highlights total household spend (strictly excluding investments) with instant cards for **Monthly Savings** (with saving %) and **Investments** (with investment allocation %).
  * **Inflow Breakdown**: Total Cash Inflow split into **Current Month Income** and **Extra From Previous Month**.
  * **Category-Wise Spending Bar Graph**: Real-time spending against allocated category budgets, variance indicators (within budget vs over budget), and interactive hover tooltips.
  * **Upcoming Annual Reminders**: Dynamic timeline countdown for annual commitments (e.g. Health Insurance, Car Insurance, LIC policies) calculating months remaining relative to any selected month.
  * **Active Loans & EMIs Highlight**: Displays monthly debt obligations (₹29,500/mo), the **Financial Thermometer** debt-to-income gauge (15.95% Safe Zone), and new EMI safe headroom (+₹7,500).

* **Analytics & Intelligence**: Member-wise spending distribution, top spend categories, cash available, and savings/investment rates.
* **Fixed Commitments & Debt Command Center**:
  * Full **Annual & One-Time Commitments** table with renewal timeline roadmap.
  * Comprehensive **EMIs & Loans** table with payoff schedules, remaining tenure, and debt thermometer.
* **Live Google Sheets Integration**: Two-way sync to log expenses, edit monthly settings, and inspect records.

### Launching the Dashboard

`ash
# Start dashboard on port 5050
python app_dashboard.py

# Or run the Windows batch launcher
run_dashboard.bat
`
Then open http://localhost:5050 in your browser.

---

## 🤝 Contributing & Community

Contributions are warmly welcome! If you'd like to add support for voice notes (speech-to-text), image bill scanning (OCR via Gemini Vision), or Telegram/Discord adapters:
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/VoiceExpenseLogger`).
3. Commit your Changes (`git commit -m 'Add voice note transcription support'`).
4. Push to the Branch (`git push origin feature/VoiceExpenseLogger`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ for Indian families managing household budgets together.
</p>
