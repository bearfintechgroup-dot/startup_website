# ============================================================
# Core Imports
# ============================================================
from flask import (
    Flask, render_template, request, redirect,
    flash, url_for, jsonify, session
)
from flask_mail import Mail, Message
from threading import Thread
from functools import wraps
from dotenv import load_dotenv
from datetime import datetime
import os
import traceback
import pandas as pd

# ============================================================
# Internal Analytics
# ============================================================
from analytics.market import fetch_market_data
from analytics.engine import analyze_market

# ============================================================
# Environment Setup
# ============================================================
load_dotenv()

# ============================================================
# Flask App Setup
# ============================================================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow}

# ============================================================
# Email Configuration
# ============================================================
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
)

mail = Mail(app)

# ============================================================
# Async Email Helper
# ============================================================
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception:
            print("\n--- EMAIL SEND ERROR ---")
            print(traceback.format_exc())
            print("------------------------\n")

# ============================================================
# Authentication Decorator
# ============================================================
def dashboard_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("dashboard_auth"):
            return redirect(url_for("dashboard_login"))
        return fn(*args, **kwargs)
    return wrapper

# ============================================================
# Routes
# ============================================================

@app.route("/")
def home():
    return render_template("index.html", active_page="home")

# -------------------------
# Dashboard Auth
# -------------------------
@app.route("/dashboard/login", methods=["GET", "POST"])
def dashboard_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw and pw == os.getenv("DASHBOARD_PASSWORD"):
            session["dashboard_auth"] = True
            return redirect(url_for("dashboard"))
        return render_template("dashboard_login.html", error="Invalid password.")

    return render_template("dashboard_login.html")

@app.route("/dashboard/logout")
def dashboard_logout():
    session.pop("dashboard_auth", None)
    return redirect(url_for("home"))

# -------------------------
# Dashboard Pages
# -------------------------
@app.route("/dashboard")
@dashboard_required
def dashboard():
    market_data = fetch_market_data()
    results = analyze_market(market_data)
    return render_template("dashboard.html", results=results)

# -------------------------
# API Endpoints (Protected)
# -------------------------
@app.route("/api/market")
@dashboard_required
def market_api():
    period = request.args.get("period", "3mo")
    market_data = fetch_market_data(period=period)
    results = analyze_market(market_data)
    return jsonify(results)

@app.route("/api/series/<symbol>")
@dashboard_required
def series_api(symbol):
    period = request.args.get("period", "3mo")
    df = fetch_market_data(symbols=[symbol], period=period).get(symbol)

    if df is None or df.empty:
        return jsonify({"error": "No data"}), 404

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = close.dropna()
    ma10 = close.rolling(10).mean()
    ma30 = close.rolling(30).mean()

    close = close.tail(120)
    ma10 = ma10.tail(120)
    ma30 = ma30.tail(120)

    return jsonify({
        "labels": [d.strftime("%Y-%m-%d") for d in close.index],
        "close": close.round(2).tolist(),
        "ma10": ma10.round(2).tolist(),
        "ma30": ma30.round(2).tolist(),
    })

# -------------------------
# Static Pages
# -------------------------
@app.route("/about")
def about():
    return render_template("about.html", active_page="about")

@app.route("/services")
def services():
    return render_template("services.html", active_page="services")

# -------------------------
# Contact Form
# -------------------------
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message_body = request.form["message"]

        admin_msg = Message(
            subject=f"New Contact Form Submission from {name}",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]],
            body=f"Name: {name}\nEmail: {email}\n\n{message_body}"
        )

        user_msg = Message(
            subject="Thank you for contacting BEAR FINTECH GROUP",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email],
            body=(
                f"Hi {name},\n\n"
                "Thank you for reaching out to BEAR FINTECH GROUP.\n"
                "Your message has been received.\n\n"
                "— BEAR FINTECH GROUP"
            )
        )

        try:
            Thread(target=send_async_email, args=(app, admin_msg)).start()
            Thread(target=send_async_email, args=(app, user_msg)).start()
            flash("Message sent successfully!", "success")
        except Exception as e:
            flash("An error occurred while sending your message.", "danger")
            print(e)

        return redirect(url_for("contact"))

    return render_template("contact.html", active_page="contact")

# ============================================================
# Error Pages
# ============================================================
@app.errorhandler(404)
def page_not_found(_):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(_):
    return render_template("500.html"), 500

# ============================================================
# Development Entry Point
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
