from __future__ import annotations

import os
import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path

SNAPSHOT_CID = "ai_daily_snapshot"


class EmailConfigError(RuntimeError):
    pass


def build_email_html(report_date: date, report_url: str | None, snapshot_path: Path | None) -> str:
    if report_url:
        report_link = f'<p><a href="{report_url}">打开 Web 报告</a></p>'
    else:
        report_link = "<p>尚未配置公网 REPORT_BASE_URL，Web 报告请在本机 site/daily 目录查看。</p>"
    snapshot_html = ""
    if snapshot_path and snapshot_path.exists():
        snapshot_html = (
            f'<p><img src="cid:{SNAPSHOT_CID}" alt="AI日报快照" '
            'style="width: 100%; max-width: 1440px; border: 1px solid #e5e7eb; border-radius: 8px;" /></p>'
        )
    else:
        snapshot_html = "<p>快照生成失败，但网页报告已生成。</p>"
    return f"""
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #171717;">
        <h1>AI日报 {report_date.isoformat()}</h1>
        <p>今日报告已生成，包含官方公告、中文媒体、产业媒体、GitHub 趋势和论文来源的高热条目。</p>
        {snapshot_html}
        {report_link}
      </body>
    </html>
    """


def send_email(subject: str, html: str, snapshot_path: Path | None = None) -> None:
    to = os.getenv("EMAIL_TO")
    sender = os.getenv("EMAIL_FROM")
    if not to or not sender:
        raise EmailConfigError("EMAIL_TO and EMAIL_FROM are required when --send is used.")
    recipients = _parse_recipients(to)
    resend_key = os.getenv("RESEND_API_KEY")
    if resend_key:
        _send_resend(resend_key, sender, recipients, subject, html)
        return
    _send_smtp(sender, recipients, subject, html, snapshot_path)


def _parse_recipients(value: str) -> list[str]:
    recipients = [item.strip() for item in value.replace(";", ",").split(",")]
    return [item for item in recipients if item]


def _send_resend(api_key: str, sender: str, recipients: list[str], subject: str, html: str) -> None:
    import resend

    resend.api_key = api_key
    resend.Emails.send({"from": sender, "to": recipients, "subject": subject, "html": html})


def _send_smtp(
    sender: str,
    recipients: list[str],
    subject: str,
    html: str,
    snapshot_path: Path | None,
) -> None:
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    if not host or not username or not password:
        raise EmailConfigError("RESEND_API_KEY or SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD is required.")
    port = int(os.getenv("SMTP_PORT", "587"))
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content("AI 态势日报已生成，请打开 Web 报告查看。")
    message.add_alternative(html, subtype="html")
    if snapshot_path and snapshot_path.exists():
        html_part = message.get_payload()[-1]
        html_part.add_related(
            snapshot_path.read_bytes(),
            maintype="image",
            subtype="png",
            cid=f"<{SNAPSHOT_CID}>",
            filename="snapshot.png",
            disposition="inline",
        )
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port) as smtp:
        if os.getenv("SMTP_USE_TLS", "true").lower() == "true":
            smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)
