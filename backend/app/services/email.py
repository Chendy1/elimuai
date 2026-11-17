"""Outbound email. Development prints to the log; production needs a real provider."""
import logging
from typing import Protocol

from app.core.config import get_settings

log = logging.getLogger("elimuai.email")


class EmailSender(Protocol):
    def send_password_reset(self, to: str, reset_url: str) -> None: ...


class ConsoleEmailSender:
    def send_password_reset(self, to: str, reset_url: str) -> None:
        log.warning("DEV EMAIL to=%s password reset link: %s", to, reset_url)


_console = ConsoleEmailSender()


def get_email_sender() -> EmailSender:
    if get_settings().app_env == "production":
        raise RuntimeError("No production email provider configured")
    return _console
