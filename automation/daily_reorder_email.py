"""Daily Reorder Email Automation (standalone script)

Runs outside Streamlit.

Schedule recommendation:
  - Daily at 9:00 AM
  - Works with GitHub Actions / cron / Windows Task Scheduler

Environment variables required (either via .env or scheduler):
  - NEON_HOST
  - NEON_DATABASE
  - NEON_USER
  - NEON_PASSWORD

  - EMAIL_SMTP_SERVER
  - EMAIL_SMTP_PORT
  - EMAIL_SMTP_EMAIL
  - EMAIL_SMTP_PASSWORD
  - REORDER_EMAIL

Optional:
  - REORDER_EMAIL_SUBJECT (default: "Pharmacy Reorder Alert")
"""

import os
from datetime import datetime
import psycopg2
import pandas as pd
from dotenv import load_dotenv

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib


load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("NEON_HOST"),
        database=os.getenv("NEON_DATABASE"),
        user=os.getenv("NEON_USER"),
        password=os.getenv("NEON_PASSWORD"),
        sslmode="require",
        connect_timeout=10,
    )


def fetch_immediate_reorder_csv_dataset():
    conn = get_connection()
    try:
        query = """
        SELECT
            d.drug_id,
            d.drug_name,
            COALESCE(r.suggested_reorder_qty, 0)::INT AS suggested_reorder_quantity,
            d.manufacturer_name,
            d.manufacturer_phone AS manufacturer_contact
        FROM inventory_snapshots i
        JOIN drugs d ON i.drug_id = d.drug_id
        JOIN reorder_points r ON i.drug_id = r.drug_id
        WHERE CAST(i.snapshot_date AS DATE) = CURRENT_DATE
          AND i.remaining_stock <= r.reorder_point
        ORDER BY d.drug_id ASC;
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()


def send_email_with_csv(csv_bytes: bytes, filename: str, recipient_email: str, subject: str, body_text: str):
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT"))
    smtp_email = os.getenv("EMAIL_SMTP_EMAIL")
    smtp_password = os.getenv("EMAIL_SMTP_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = smtp_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(csv_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(attachment)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)


def main():
    recipient = os.getenv("REORDER_EMAIL")
    if not recipient:
        raise SystemExit("Missing env var: REORDER_EMAIL")

    df = fetch_immediate_reorder_csv_dataset()
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    subject = os.getenv("REORDER_EMAIL_SUBJECT", "Pharmacy Reorder Alert")
    body_text = (
        "These drugs need to be reordered.\n\n"
        "Please find the attached CSV file containing reorder details.\n\n"
        "Generated automatically by the Pharmacy Smart Inventory System.\n\n"
        f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    filename = f"reorder_list_immediate_{datetime.now().strftime('%Y%m%d')}.csv"

    # If nothing to reorder, still email an empty list for audit.
    send_email_with_csv(csv_bytes, filename, recipient, subject, body_text)


if __name__ == "__main__":
    main()

