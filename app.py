from flask import Flask, render_template, request, redirect, flash
from flask_mail import Mail, Message
import traceback
import datetime
from flask import current_app
import os
from threading import Thread
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
        name = request.form["name"]
        email = request.form["email"]
        message_body = request.form["message"]

        msg = Message(
            subject=f"New Contact Form Submission from {name}",
            sender=app.config['MAIL_USERNAME'],
            recipients=[app.config['MAIL_USERNAME']],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"
        )

        try:
            # send email in a background thread
            Thread(target=send_async_email, args=(app, msg)).start()
            flash("Message sent successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")

        return redirect("/contact")

    return render_template("contact.html")


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

if __name__ == "__main__":
    app.run(debug=True)
