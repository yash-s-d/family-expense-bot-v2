"""
Flask Webhook Server for Meta WhatsApp Cloud API.
Receives webhook events from Meta, resolves sender to family member, and replies.
"""
import os
from flask import Flask, request, jsonify
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import normalize_person, get_phone_to_person_map
from main import handle_message
from whatsapp_client import send_whatsapp_message

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "family_expense_secret_token")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify(status="ok", service="Family Expense Bot Webhook"), 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Meta Webhook Verification handshake.
    Meta calls this endpoint when you configure the Callback URL in the Developer Dashboard.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[Webhook Verification] Successfully verified by Meta!")
        return challenge, 200

    print(f"[Webhook Verification FAILED] Received token '{token}', expected '{VERIFY_TOKEN}'")
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    """
    Handles inbound WhatsApp messages forwarded by Meta.
    """
    data = request.get_json(silent=True) or {}

    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        # Ignore status updates (e.g. message sent, delivered, read receipts)
        if not messages:
            return jsonify(status="ignored - no messages"), 200

        msg = messages[0]
        sender_phone = msg.get("from", "")
        msg_type = msg.get("type", "")

        # We currently process text messages
        if msg_type != "text":
            send_whatsapp_message(
                sender_phone,
                "The bot currently accepts text messages only. Please type your expense (e.g. 'bought eggs 60 rs')."
            )
            return jsonify(status="ignored - non-text message"), 200

        text = msg.get("text", {}).get("body", "").strip()
        if not text:
            return jsonify(status="ignored - empty text"), 200

        # Map phone number to family member
        phone_map = get_phone_to_person_map()
        person = phone_map.get(sender_phone)

        if not person:
            # Sender is not in the recognized family list
            print(f"[Unrecognized sender]: {sender_phone}")
            send_whatsapp_message(
                sender_phone,
                f"Hello! Your number (+{sender_phone}) is not recognized as a registered family member yet.\n"
                f"Please add your phone number to PHONE_TANMAY, PHONE_AKSHAT, PHONE_AAI, or PHONE_DAD in .env."
            )
            return jsonify(status="unregistered sender"), 200

        canonical_person = normalize_person(person)
        print(f"[Incoming Expense] From: {canonical_person} ({sender_phone}) | Message: '{text}'")

        # Process expense message
        reply = handle_message(text, canonical_person)

        # Send confirmation reply back to the sender
        send_whatsapp_message(sender_phone, reply)
        return jsonify(status="ok"), 200

    except (KeyError, IndexError, Exception) as e:
        print(f"Error handling webhook payload: {e}\nPayload: {data}")
        return jsonify(status="error", error=str(e)), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Family Expense Bot Webhook on port {port}...")
    print(f"Webhook URL: http://localhost:{port}/webhook")
    print(f"Verify Token configured: '{VERIFY_TOKEN}'")
    app.run(host="0.0.0.0", port=port, debug=True)
