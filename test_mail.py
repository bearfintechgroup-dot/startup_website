from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME='bearfintechgroup@gmail.com',       # your Gmail
    MAIL_PASSWORD='oeimjtpmfgvewzbj'   # App Password
)

mail = Mail(app)

with app.app_context():
    msg = Message(
        subject="Test Email from Flask",
        sender=app.config['MAIL_USERNAME'],
        recipients=[app.config['MAIL_USERNAME']],
        body="This is a test email from Flask-Mail."
    )
    try:
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
