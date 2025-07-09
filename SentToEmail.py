import smtplib
from email.message import EmailMessage
import os

def send_email_with_report(to_email, subject, body, attachment_path):
    # Set up your email credentials and SMTP server
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # Your email address
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your email password or app password
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(body)

    # Attach the report
    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)
    msg.add_attachment(file_data, maintype="text", subtype="markdown", filename=file_name)

    # Send the email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print(f"Report sent to {to_email}")
