from flask import Flask, render_template, request, redirect, flash, url_for
from flask_mail import Mail, Message
from threading import Thread
from dotenv import load_dotenv
import os
import traceback
from datetime import datetime
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
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


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

    return render_template("contact.html")

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
