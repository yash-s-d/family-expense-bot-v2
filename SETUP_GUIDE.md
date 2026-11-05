# Step-by-Step Setup Guide: WhatsApp Family Expense Bot

Follow this complete guide to get all the keys, tokens, and test numbers required to run your WhatsApp bot.

---

## Step 1: Get Google Gemini API Key (Free)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey).
2. Sign in with your Google Account.
3. Click **"Create API Key"**.
4. Choose any Google Cloud project or click **"Create key in new project"**.
5. Copy the generated key.
6. Open your `.env` file and set:
   ```env
   GEMINI_API_KEY=AIzaSy...your_key_here
   ```

---

## Step 2: Set Up Google Cloud Service Account & Sheet Sharing

To allow the bot to write directly to your Google Sheet (`1exQhj85Sv-Hhp8_Fna9qgydgYFYwZaoLRE2RnsRQ3eY`):

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one), e.g. named `Family-Expense-Tracker`.
3. In the top search bar, search for and enable these two APIs:
   - **Google Sheets API** -> Click **Enable**.
   - **Google Drive API** -> Click **Enable**.
4. Go to **IAM & Admin** > **Service Accounts** (left sidebar).
5. Click **+ CREATE SERVICE ACCOUNT**.
   - Name: `expense-bot-writer`
   - Click **Create and Continue**, then click **Done**.
6. In the Service Accounts list, click on the newly created service account email (it will look like `expense-bot-writer@your-project.iam.gserviceaccount.com`).
7. Go to the **Keys** tab -> Click **Add Key** > **Create new key** -> Choose **JSON** -> Click **Create**.
8. A `.json` file will download to your computer.
   - Move this file to a safe location (e.g., inside your project directory as `google_service_account.json` or in your user home folder).
   - In `.env`, set:
     ```env
     GOOGLE_SERVICE_ACCOUNT_JSON_PATH=C:\full\path\to\google_service_account.json
     GOOGLE_SHEET_ID=1exQhj85Sv-Hhp8_Fna9qgydgYFYwZaoLRE2RnsRQ3eY
     ```
9. **CRITICAL STEP**: Open your Google Sheet in your browser:
   - URL: `https://docs.google.com/spreadsheets/d/1exQhj85Sv-Hhp8_Fna9qgydgYFYwZaoLRE2RnsRQ3eY/edit`
   - Click the blue **Share** button in the top right.
   - Paste the service account email (`expense-bot-writer@your-project.iam.gserviceaccount.com`).
   - Set permission to **Editor** and click **Send** (uncheck "Notify people" if prompted).

---

## Step 3: Meta WhatsApp Cloud API Setup (Free Test Number)

1. Go to [developers.facebook.com](https://developers.facebook.com/) and log in with your Facebook account.
2. Click **My Apps** > **Create App**.
   - Select **Other** as the use case.
   - Select **Business** as the app type.
   - Enter an app name (e.g., `Family Expense Bot`) and your email.
3. On the App Dashboard, scroll down to **"Add products to your app"** and find **WhatsApp** -> click **Set up**.
4. On the WhatsApp **API Setup** page, Meta gives you:
   - **Temporary Access Token**: Copy this into `WHATSAPP_ACCESS_TOKEN` in `.env`.
   - **Phone number ID**: Copy this into `WHATSAPP_PHONE_NUMBER_ID` in `.env`.
   - **Test Phone Number**: This is the WhatsApp number your family will message!
5. **Add Family Numbers to Allowlist (Crucial for Free Test Number)**:
   - Under the **"To"** field dropdown, click **Manage phone number list**.
   - Add the WhatsApp mobile numbers of:
     - Tanmay
     - Akshat
     - Aai
     - Dad
   - Meta will send a 6-digit verification code via WhatsApp to each number. Enter the codes to verify them.
6. In `.env`, add the phone numbers with country code (e.g. `91` for India) and no `+` sign:
   ```env
   PHONE_TANMAY=919876543210
   PHONE_AKSHAT=919876543211
   PHONE_AAI=919876543212
   PHONE_DAD=919876543213
   ```
7. Set a verify token of your choice in `.env`:
   ```env
   WHATSAPP_VERIFY_TOKEN=my_family_secret_token_123
   ```

---

## Step 4: Run Webhook Locally with ngrok

1. Open a terminal and run the Flask webhook server:
   ```bash
   python webhook_server.py
   ```
   (Starts on `http://localhost:5000`)

2. In a second terminal, start ngrok to create a secure public URL:
   ```bash
   ngrok http 5000
   ```
   (Ngrok gives you a public URL like `https://abcdef123.ngrok-free.app`)

3. Connect Webhook in Meta Developer Dashboard:
   - In your Meta Developer App, go to **WhatsApp** > **Configuration** (left sidebar).
   - In the **Webhook** section, click **Edit**:
     - **Callback URL**: `https://abcdef123.ngrok-free.app/webhook`
     - **Verify Token**: whatever you set in `.env` (e.g. `my_family_secret_token_123`).
   - Click **Verify and Save**. (Meta will ping your local server and verify instantly!).
   - In the **Webhook fields** table below, click **Manage** and subscribe to **messages**.

---

## Step 5: Test from WhatsApp!

1. From any verified phone (Tanmay, Akshat, Aai, or Dad), open WhatsApp.
2. Send a message to the Meta test number:
   > *"bought eggs 60 rs"*
3. Within 2-3 seconds, the bot will reply:
   > *"✅ Logged ₹60 for eggs under Groceries for Tanmay (row 8)."*
4. Open your Google Sheet to confirm the row was added under the current month tab!
