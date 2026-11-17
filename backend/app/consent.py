"""Versioned consent notice. The TEXT BELOW IS A DRAFT PLACEHOLDER, not legal wording.

The final notice must be written after legal review and a Data Protection Impact Assessment, and
before any real learner is added. Changing the text requires a new NOTICE_VERSION.
"""
import hashlib

NOTICE_VERSION = "0.1-draft"
NOTICE_TITLE = "Consent to create a learner profile (DRAFT)"
NOTICE_TEXT = (
    "DRAFT PLACEHOLDER. This is not the final legal notice.\n\n"
    "By continuing, you confirm that you are the parent or legal guardian of this learner and "
    "that you agree to ElimuAI creating a learner profile with a nickname and a grade. ElimuAI "
    "will also record the learner's learning activity so it can show progress.\n\n"
    "We intend to collect only what is needed, never to sell children's data, and never to use "
    "learning conversations for advertising. You will be able to change or remove the profile at "
    "any time, which withdraws this consent.\n\n"
    "Final wording, retention periods and data-transfer details will be added after legal review."
)
PURPOSE = "learner_profile"


def notice_sha256() -> str:
    """Fingerprint of the exact text the guardian saw, stored with each consent record."""
    return hashlib.sha256(NOTICE_TEXT.encode()).hexdigest()
