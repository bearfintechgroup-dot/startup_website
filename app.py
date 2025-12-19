from flask import Flask, render_template, request, redirect, flash, url_for
from flask_mail import Mail, Message
from threading import Thread
from dotenv import load_dotenv
import os
import traceback
from datetime import datetime
from analytics.market import fetch_market_data
from analytics.engine import analyze_market
from flask import jsonify
import pandas as pd
from flask import session, redirect


# -----------------------------------------
# Load environment variables
# -----------------------------------------
load_dotenv()


# -----------------------------------------
# App Setup
# -----------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "fallback-secret"

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}


# -----------------------------------------
# Email Configuration (Gmail SMTP)
# -----------------------------------------
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
)

mail = Mail(app)


# -----------------------------------------
# Async Email Sending
# -----------------------------------------
def send_async_email(app, msg):
    """Send email in a background thread."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print("\n--- EMAIL SEND ERROR ---")
            print(e)
            print(traceback.format_exc())
            print("------------------------\n")


# -----------------------------------------
# Routes
# -----------------------------------------

@app.route("/")
def home():
    return render_template("index.html", active_page="home")

def dashboard_required(fn):
    def wrapper(*args, **kwargs):
        if not session.get("dashboard_auth"):
            return redirect(url_for("dashboard_login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@app.route("/dashboard/login", methods=["GET", "POST"])
def dashboard_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw and pw == os.getenv("DASHBOARD_PASSWORD"):
            session["dashboard_auth"] = True
            return redirect("/dashboard")
        return render_template("dashboard_login.html", error="Invalid password.")
    return render_template("dashboard_login.html")

@app.route("/dashboard/logout")
def dashboard_logout():
    session.pop("dashboard_auth", None)
    return redirect("/")

@app.route("/dashboard")
@dashboard_required
def dashboard():
    market_data = fetch_market_data() # from analytics.market
    results = analyze_market(market_data)

    return render_template(
        "dashboard.html",
        results=results
    )


@app.route("/api/market")
@dashboard_required
def market_api():
    period = request.args.get("period", "3mo")  # e.g. 5d, 1mo, 6mo, 1y
    market_data = fetch_market_data(period=period)
    results = analyze_market(market_data)
    return jsonify(results)

@app.route("/api/series/<symbol>")
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

    # Keep last ~120 points for speed
    close = close.tail(120)
    ma10  = ma10.tail(120)
    ma30  = ma30.tail(120)

    labels = [d.strftime("%Y-%m-%d") for d in close.index]
    return jsonify({
        "labels": labels,
        "close": [float(x) if x == x else None for x in close.values],
        "ma10":  [float(x) if x == x else None for x in ma10.values],
        "ma30":  [float(x) if x == x else None for x in ma30.values],
    })

@app.route("/about")
def about():
    return render_template("about.html", active_page="about")


@app.route("/services")
def services():
    return render_template("services.html", active_page="services")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message_body = request.form["message"]

        # ---------------------------
        # 1. Email sent TO YOU
        # ---------------------------
        admin_msg = Message(
            subject=f"New Contact Form Submission from {name}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"
        )

        # ---------------------------
        # 2. Confirmation email sent TO USER
        # ---------------------------
        user_msg = Message(
            subject="Thank you for contacting BEAR FINTECH GROUP",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email],
            body=(
                f"Hi {name},\n\n"
                "Thank you for reaching out to BEAR FINTECH GROUP.\n"
                "Your message has been received successfully.\n\n"
                "We will respond shortly.\n\n"
                "Best regards,\n"
                "BEAR FINTECH GROUP"
            )
        )

        try:
            Thread(target=send_async_email, args=(app, admin_msg)).start()
            Thread(target=send_async_email, args=(app, user_msg)).start()

            flash("Message sent successfully!", "success")

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
            print("EMAIL ERROR:", e)

        return redirect("/contact")

    return render_template("contact.html", active_page="contact")


# ----------------------------
# Custom Error Pages
# ----------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500

# -----------------------------------------
# Run Application (local only)
# -----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
