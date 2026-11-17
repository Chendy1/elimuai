# ADR 0006: Learners are guardian-managed profiles with no login (for now)
Status: Accepted (Phase 2.2) · Revisit: when school-created accounts or learner PINs are built

**Decision:** A learner is a profile (nickname, grade) owned by one guardian. The guardian's session acts on the learner's behalf. No learner email, password, birth date or photo is stored.
**Why:** Minimum data about children; consent sits with the guardian who creates the profile; one authentication surface to secure.
**Consent:** each profile creation stores a consent record (notice version, SHA-256 of the exact text shown, time). Removing a profile soft-deletes it and withdraws consent. The notice text is a DRAFT placeholder until legal review and the DPIA.
**Limits:** 6 learners per guardian; nicknames reject "@" and 6+ digit runs to discourage personal data.
