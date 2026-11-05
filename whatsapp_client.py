"""
WhatsApp Cloud API client for sending messages.
Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
"""
import os
import requests

GRAPH_API_VERSION = "v21.0"

def send_whatsapp_message(to: str, text: str) -> dict:
    """
    Sends a plain text WhatsApp message using Meta WhatsApp Cloud API.
    `to` must be in international format without leading '+' (e.g. '919876543210').
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()

    if not access_token or not phone_number_id:
        print("[WhatsApp Client WARNING] WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID missing.")
        return {"status": "skipped - missing credentials"}

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        if response.status_code != 200:
            print(f"WhatsApp send failed ({response.status_code}): {response.text}")
        return response.json()
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return {"error": str(e)}
