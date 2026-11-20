# Curriculum import guide (Phase 3.2)

**Rule:** source documents are copyrighted ("All rights reserved"). Keep the PDFs in the git-ignored `data/sources/` folder, never commit them or text copied from them, and do not publish anything until the source's licence status is `granted`.

## 1. Put the PDFs where the backend container can read them
`docker-compose.yml` mounts `./data` read-only at `/data`. Place files in `data\sources\` on your machine, then recreate the backend once: `docker compose up -d --force-recreate backend`.

## 2. Register a PDF and store its pages
```powershell
docker compose exec backend python -m app.cli import-source --file /data/sources/FILE.pdf --title "TITLE" --publisher "Kenya Institute of Curriculum Development" --edition "EDITION"
docker compose exec backend python -m app.cli list-sources
docker compose exec backend python -m app.cli show-page --source SOURCE_ID --page 13
```
Importing the same file again does nothing (it is identified by its SHA-256). Each page is stored with its PDF page number and, when detected, the number printed on the page. They differ (front matter, restarted numbering), so both are kept.

## 3. Check the extraction
Use `show-page` on a few pages (a cover, a contents page, a dense table page). Report anything that looks wrong before the proposer (3.2b) is built on it.

## 4. Record licence status
After KICD replies, an admin sets it: `PATCH /admin/curriculum/sources/{id}/license` with `granted`, `requested` or `denied` and a note. Publishing a curriculum version that references the source is refused until it is `granted`.

## Known extraction quirks
- Some Roman numerals in the front matter come out as unusual glyphs; the importer maps the ones seen so far.
- Cover pages have no printed number (stored as none).
- Tables are stored in layout mode (columns kept apart with spaces) so a reviewer can read them next to the draft record.

## 5. Propose draft records from a stored source (Phase 3.2b)

Supported layout: **one table per sub-strand** (the Grade 6 Mathematics design). The English design (themes, several strands per page) needs a second parser and is not supported yet; the command says so rather than guessing.

1. Create a curriculum and a draft version (admin API, or `/docs`). Note the **version id**.
2. Preview first. A dry run parses and reports, writing nothing:
```powershell
docker compose exec backend python -m app.cli propose --source SOURCE_ID --version VERSION_ID --grade-level 6 --area "Mathematics" --dry-run
```
3. If the counts look right, run it again without `--dry-run`. It creates a draft learning area with strands, sub-strands, outcomes, experiences, questions, competencies, values, PCIs and rubrics.

Every created record:
- has review status `draft` and cannot be published until a reviewer approves it,
- points at the source page it came from,
- carries a review comment listing what the parser could not place.

### What the parser flags instead of guessing
- A PCI or values paragraph with no name (the design often gives plain sentences): the text is kept in the review comment and the reviewer chooses the name.
- Mixed bullet levels (for example nested dashes under one bullet), and any case where the bullets visible in the experiences column differ from the number parsed.
- Missing lesson counts, outcome letters that are not a, b, c..., or a header it could not locate.

### Measured on the Grade 6 Mathematics design (counts only)
16 sub-strands in 4 strands, 97 outcomes, 99 experiences, 20 inquiry questions, 36 rubric rows (every row has all four levels), 16 items flagged for a human. Treat the output as a first draft: **reviewers must check each sub-strand against its source page.**

## 6. Review in the browser (Phase 3.3)

Create the curriculum and a draft version from the command line:
```powershell
docker compose exec backend python -m app.cli create-curriculum --code kenya-cbe --name "Kenya CBE"
docker compose exec backend python -m app.cli create-version --curriculum kenya-cbe --label "Draft 2026"
```
Then run `propose` (section 5) with the printed version id, and open **http://localhost:3000/admin/curriculum** signed in as a reviewer, curriculum admin or super admin.

For each learning area, strand and sub-strand: pick it on the left, compare the draft record with the **source page** shown beside it (Previous and Next page buttons follow a table across pages), then choose **Approve**, **Needs changes** or **Mark in review**. A comment is optional; approving without one keeps the importer's notes. Fix wrong values through the admin API for now (an editing screen comes later) and re-review.

Publishing (curriculum admins and super admins only) is refused until every learning area, strand and sub-strand is approved **and** every source has its licence recorded as `granted`. The page tells you what is still missing.
