"""
Family Expense Bot · Neo-Fintech Dashboard Web Application
Built with Flask, Google Sheets integration, and minimal Neo-Fintech Design System.

Run directly via:
    python app_dashboard.py
"""

import os
import sys
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Ensure local modules are found
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

load_dotenv(os.path.join(CURRENT_DIR, ".env"))

from dashboard_service import dashboard_service

app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, "templates"))

@app.route("/")
def index():
    """Renders the main Neo-Fintech dashboard interface."""
    return render_template("dashboard.html")

@app.route("/api/summary", methods=["GET"])
def api_summary():
    """Returns aggregated metrics for the requested month."""
    month = request.args.get("month", "Nov").capitalize()[:3]
    try:
        data = dashboard_service.compute_dashboard_metrics(month)
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error computing summary for {month}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/months", methods=["GET"])
def api_months():
    """Returns list of available months."""
    return jsonify(dashboard_service.get_available_months())

@app.route("/api/income-fixed", methods=["GET"])
def api_income_fixed():
    """Returns recurring income and fixed commitments."""
    return jsonify(dashboard_service.get_income_and_fixed())

@app.route("/api/update-member-settings", methods=["POST"])
def api_update_member_settings():
    """Updates member budget settings (Extra from prev month, Income) in Google Sheet."""
    payload = request.get_json(force=True) or {}
    month = payload.get("month", "Nov").capitalize()[:3]
    settings = payload.get("settings", {})
    try:
        res = dashboard_service.update_member_settings_in_sheet(month, settings)
        return jsonify(res)
    except Exception as e:
        app.logger.error(f"Failed to update member settings: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/add-expense", methods=["POST"])
def api_add_expense():
    """Appends a new expense to the Google Sheet."""
    payload = request.get_json(force=True) or {}
    month = payload.get("month", "Nov").capitalize()[:3]
    date_str = payload.get("date", "")
    description = payload.get("description", "").strip()
    category = payload.get("category", "Miscellaneous / Other")
    amount = float(payload.get("amount", 0))
    paid_by = payload.get("paid_by", "Tanmay")
    comment = payload.get("comment", "")

    if not description or amount <= 0:
        return jsonify({"error": "Description and positive amount are required."}), 400

    try:
        res = dashboard_service.add_expense(
            month_abbr=month,
            date_str=date_str,
            description=description,
            category=category,
            amount=amount,
            paid_by=paid_by,
            comment=comment
        )
        return jsonify(res)
    except Exception as e:
        app.logger.error(f"Failed to append row: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Flushes cache and reloads from Google Sheet."""
    month = request.args.get("month")
    dashboard_service.invalidate_cache(month)
    return jsonify({"success": True, "message": "Cache invalidated"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"Starting Neo-Fintech Family Finance Dashboard on http://localhost:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)
