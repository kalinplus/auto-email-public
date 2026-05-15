import smtplib
import time
from datetime import datetime, timezone
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from config import Config

SEND_INTERVAL_SECONDS = 10


def send_emails(advisors: list[dict], config: Config) -> list[dict]:
    pending = [a for a in advisors if a.get("sent") is not True]
    if not pending:
        return advisors

    if config.smtp_port == 465:
        server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port)
    else:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()

    try:
        server.login(config.smtp_user, config.smtp_pass)
        for i, advisor in enumerate(pending):
            if i > 0:
                time.sleep(SEND_INTERVAL_SECONDS)

            msg = MIMEMultipart("mixed")
            msg["Subject"] = Header(advisor["email_subject"], "utf-8")
            msg["From"] = formataddr((config.sender_name, config.smtp_user))
            msg["To"] = advisor["email"]

            msg.attach(MIMEText(advisor["email_body"], "plain", "utf-8"))

            with open(config.cv_path, "rb") as f:
                att = MIMEApplication(f.read(), _subtype="pdf")
                att.add_header("Content-Type", "application/pdf", name="CV.pdf")
                att.add_header("Content-Disposition", "attachment", filename="CV.pdf")
                msg.attach(att)

            try:
                server.sendmail(config.smtp_user, advisor["email"], msg.as_string())
                advisor["sent"] = True
                advisor["sent_at"] = datetime.now(timezone.utc).isoformat()
            except (smtplib.SMTPException, OSError) as e:
                advisor["error"] = str(e)
    except smtplib.SMTPAuthenticationError:
        raise
    finally:
        server.quit()

    return advisors
