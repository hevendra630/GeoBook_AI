

import sys

import os

from datetime import datetime

sys.path.append(os.path.abspath("."))

try:

    from app.services.emailer import send_email

    from app.core.config import settings

    

    print("--- SMTP CONFIGURATION CHECK ---")

    print(f"Host: {settings.smtp_host}")

    print(f"Port: {settings.smtp_port}")

    print(f"User: {settings.smtp_username}")

    print(f"From: {settings.smtp_from_email}")

    print("--------------------------------")

    

    test_receiver = settings.smtp_from_email

    if not test_receiver:

        print("ERROR: SMTP_FROM_EMAIL is not set in .env")

        sys.exit(1)

    print(f"Sending test email to: {test_receiver}...")

    

    send_email(

        to_email=test_receiver,

        subject="GeoBook AI - SMTP Test",

        body=f"This is a test email from your GeoBook AI assistant.\nSent at: {datetime.now()}"

    )

    

    print("SUCCESS: Check your inbox!")

except Exception as e:

    print(f"FAILURE: {str(e)}")

    import traceback

    traceback.print_exc()

