from flask import Flask, render_template, request, redirect, flash, url_for
from flask_mail import Mail, Message
from threading import Thread
from dotenv import load_dotenv
import os
import traceback

# -----------------------------------------
# Load environment variables
# -----------------------------------------
load_dotenv()


# -----------------------------------------
# App Setup
# -----------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "fallback-secret"


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
        name = request.form.get("name")
        email = request.form.get("email")
        message_body = request.form.get("message")

        # Validate email fields exist
        if not name or not email or not message_body:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("contact"))

        # Create email message
        msg = Message(
            subject=f"New Contact Form Submission from {name}",
            sender=app.config["MAIL_USERNAME"],
            recipients=[app.config["MAIL_USERNAME"]],
            body=f"""
New contact form submission:

Name: {name}
Email: {email}

Message:
{message_body}
""",
        )

        # Try sending email
        try:
            Thread(target=send_async_email, args=(app, msg)).start()
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            print("\n--- EMAIL ERROR ---")
            print(e)
            print(traceback.format_exc())
            print("-------------------\n")
            flash("An error occurred while sending your message. Please try again.", "danger")

        return redirect(url_for("contact"))

    return render_template("contact.html")


# -----------------------------------------
# Run Application (local only)
# -----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
