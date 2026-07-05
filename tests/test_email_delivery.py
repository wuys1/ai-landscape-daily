from __future__ import annotations

import pytest

from ai_landscape_daily.email.delivery import EmailConfigError, _parse_recipients, send_email


def test_send_email_requires_recipients(monkeypatch):
    monkeypatch.delenv("EMAIL_TO", raising=False)
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")

    with pytest.raises(EmailConfigError, match="EMAIL_TO and EMAIL_FROM"):
        send_email("subject", "<p>hello</p>")


def test_parse_recipients_accepts_comma_and_semicolon_lists():
    recipients = _parse_recipients("one@example.com, two@example.com;three@example.com")

    assert recipients == ["one@example.com", "two@example.com", "three@example.com"]
