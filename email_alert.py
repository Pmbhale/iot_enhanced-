import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -------------------------------------------------
# PUT YOUR DETAILS HERE (GET APP PASSWORD FROM GOOGLE)
# -------------------------------------------------
SENDER_EMAIL = "parthbhale1247@gmail.com"
APP_PASSWORD = "qtfh vmme vgbq kztr"  # ← Get this from Google App Passwords
RECEIVER_EMAIL = "parthbhale1234@gmail.com"


# -------------------------------------------------

def send_email(subject, message, receiver_email=None):
    """Send email using Gmail SMTP"""

    # Use default receiver if none provided
    if receiver_email is None:
        receiver_email = RECEIVER_EMAIL

    # Create message
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email

    # Add body
    msg.attach(MIMEText(message, 'plain'))

    try:
        # Connect to Gmail SMTP server
        print(f"Attempting to send email from {SENDER_EMAIL} to {receiver_email}")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {receiver_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


# Test function
if __name__ == "__main__":
    # Test the email function
    print("Testing email module...")
    result = send_email(
        subject="Test Email from Critical Monitoring",
        message="This is a test email to verify the email module is working correctly.\n\nSystem Time: Test"
    )
    print(f"Test result: {'Success' if result else 'Failed'}")