# ADR 0008: Curriculum model, review workflow and publishing gates
Status: Accepted (Phase 3.1)

**Model:** Curriculum > Version > Grade > Learning area > [optional Unit] > Strand > Sub-strand > topics, outcomes, experiences, inquiry questions, competencies, values, PCIs; rubric indicators sit on strands. The optional *unit* level exists because the Grade 6 English design groups strands under themes while Mathematics does not. No hierarchy is hardcoded in the frontend.
**Official vs internal levels:** rubric indicators store the official four performance levels (Exceeds, Meets, Approaches, Below Expectations). ElimuAI's own mastery states live elsewhere and are never mixed with them.
**Review:** learning areas, units, strands and sub-strands each carry `review_status` (draft, in_review, approved, rejected), reviewer, time, comment and a source-page reference. Content is only editable while its version is a draft.
**Publishing gates (all enforced in the backend):** (1) every non-archived node must be approved; (2) the version must contain at least one sub-strand; (3) every source document referenced by any node must have `license_status = granted`. Publishing a version archives the previously published one; a partial unique index guarantees one published version per curriculum.
**Why gate 3:** the official designs are marked "All rights reserved ... without prior written permission". Recording permission in the system makes it impossible to publish imported content by accident.
**Reads:** learners see only a published version, only when signed in, and only approved, non-archived areas.
**Content stays out of Git:** source PDFs live in a git-ignored `data/` folder; tests use obviously fake demo content.
