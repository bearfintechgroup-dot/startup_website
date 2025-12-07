from flask import Flask, render_template, request, redirect, flash
from flask_mail import Mail, Message
import traceback
import datetime
from flask import current_app
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


# ----------------------------
# Flask-Mail configuration
# ----------------------------
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD")
)

mail = Mail(app)

# ----------------------------
# Routes
# ----------------------------
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
        # Get form safely (use .get to avoid KeyError if field missing)
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message_body = request.form.get("message", "").strip()

        # Basic validation: require name/email/message
        if not name or not email or not message_body:
            flash("Please complete all fields before sending.", "danger")
            return redirect("/contact")

        # Save the message locally as a fallback (append)
        try:
            ts = datetime.datetime.utcnow().isoformat()
            with open("sent_messages.log", "a", encoding="utf-8") as f:
                f.write(f"[{ts}] Name: {name} | Email: {email}\n{message_body}\n\n")
        except Exception as file_err:
            # Log but don't block sending
            app.logger.error("Failed to write fallback message: %s", file_err)

        # Prepare the email
        msg = Message(
            subject=f"New Contact Form Submission from {name}",
            sender=app.config.get('MAIL_USERNAME'),
            recipients=[app.config.get('MAIL_USERNAME')],  # send to yourself
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"
        )

        # Try sending the email & log full traceback if it fails
        try:
            mail.send(msg)
            flash("Message sent successfully!", "success")
        except Exception as e:
            # Log full traceback to PyCharm console (very useful)
            app.logger.error("Exception while sending email:\n%s", traceback.format_exc())
            # Show a user-friendly message
            flash("There was a problem sending your message; it has been saved and I will be notified.", "danger")

        return redirect("/contact")

    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)
