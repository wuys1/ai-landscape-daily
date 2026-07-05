from __future__ import annotations

from ai_landscape_daily.email.delivery import DEFAULT_RECIPIENTS, _parse_recipients


def test_parse_recipients_uses_default_list_when_unset():
    assert _parse_recipients(None) == DEFAULT_RECIPIENTS
    assert _parse_recipients("") == DEFAULT_RECIPIENTS


def test_parse_recipients_accepts_comma_and_semicolon_lists():
    recipients = _parse_recipients("one@example.com, two@example.com;three@example.com")

    assert recipients == ["one@example.com", "two@example.com", "three@example.com"]
