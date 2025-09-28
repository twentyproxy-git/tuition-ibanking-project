from __future__ import print_function
import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
from zoneinfo import ZoneInfo

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.compose']

def load_template(filename: str, context: dict = None):
    with open(filename, "r", encoding="utf-8") as f:
        template = f.read()
    if context:
        for key, value in context.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
    return template

def send_email_v1(recipient, subject, html_content):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            raise Exception("No valid credentials. Vui lòng tạo token.json ngoài Docker.")

    try:
        service = build('gmail', 'v1', credentials=creds)

        message = EmailMessage()
        message['Subject'] = subject
        message['To'] = recipient
        message['From'] = formataddr(('IBanking Bot',
                                      service.users().getProfile(userId='me').execute()['emailAddress']))

        message.set_content("Nếu bạn không xem được HTML, đây là nội dung fallback.")

        message.add_alternative(html_content, subtype="html")

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        service.users().messages().send(userId="me", body=create_message).execute()
        return True
    except HttpError as e:
        print(f'Error occurred: {e}')
        return False

def send_otp_email(recipient: str, otp: str, full_name: str):
    subject = "OTP Code for Payment Verification"
    html_template = load_template("otp_template.html", {
        "name": full_name,
        "otp": otp
    })
    return send_email_v1(recipient, subject, html_template)

def send_transaction_email(recipient: str, full_name: str, debit: str, content: str):
    subject = "Transaction Notification"
    vn_timezone = ZoneInfo("Asia/Ho_Chi_Minh")
    curr_time = datetime.now(vn_timezone).strftime("%Y-%m-%d %H:%M:%S")
    debit_value = int(debit)
    debit_str = "{:,.0f}".format(debit_value).replace(",", ".")
    html_template = load_template("transaction_template.html", {
        "name": full_name,
        "debit": debit_str,
        "content": content,
        "time": curr_time
    })
    return send_email_v1(recipient, subject, html_template)



