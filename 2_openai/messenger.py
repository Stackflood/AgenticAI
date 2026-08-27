from dotenv import load_dotenv
import requests
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_FILE, override=True)


EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_SMTP_SERVER = (os.getenv("EMAIL_SMTP_SERVER") or "").strip()
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

if not EMAIL_SMTP_SERVER:
    raise RuntimeError(
        f"EMAIL_SMTP_SERVER is missing. Add it to {ENV_FILE} (for Gmail: smtp.gmail.com)."
    )

def send_email(subject, text_body, html_body):
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)        

def send_email_extra(name, subject, text_body, html_body, signature):
    from email.utils import formataddr

    msg = EmailMessage()
    msg["From"] = formataddr((name, EMAIL_ADDRESS))
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = subject
    msg.set_content(f"{text_body}\n\n{signature}")
    msg.add_alternative(f"{html_body}<p>{signature}</p>", subtype="html")

    with smtplib.SMTP(EMAIL_SMTP_SERVER, 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)


pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"

def push(message):
    print(f"Push: {message}")
    payload = {"user": pushover_user, "token": pushover_token, "message": message}
    requests.post(pushover_url, data=payload)

