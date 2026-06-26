import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


class EmailUtils:
    """Email helper utilities for Streamlit flows."""

    @staticmethod
    def _get_smtp_config():
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        smtp_email = st.secrets["email"]["smtp_email"]
        smtp_password = st.secrets["email"]["smtp_password"]
        recipient_email = st.secrets["email"]["recipient_email"]
        return smtp_server, int(smtp_port), smtp_email, smtp_password, recipient_email

    @staticmethod
    def send_reorder_email_with_csv(
        csv_bytes: bytes,
        filename: str,
        subject: str,
        body_text: str,
        recipient_email: str = None,
    ) -> bool:
        """Send reorder email with CSV attachment.

        Secrets format expected:
          st.secrets["email"] = {
            "smtp_server": str,
            "smtp_port": int/str,
            "smtp_email": str,
            "smtp_password": str,
            "recipient_email": str
          }
        """
        try:
            smtp_server, smtp_port, smtp_email, smtp_password, default_recipient = EmailUtils._get_smtp_config()
            if recipient_email is None:
                recipient_email = default_recipient

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

            return True

        except KeyError as e:
            raise Exception(f"Missing secret key for email: {e}. Check .streamlit/secrets.toml")
        except smtplib.SMTPAuthenticationError:
            raise Exception("❌ SMTP Authentication Failed. Check your email/password.")
        except smtplib.SMTPException as e:
            raise Exception(f"❌ SMTP Error: {e}")
        except Exception as e:
            raise Exception(f"❌ Email Error: {e}")

