"""Operator commands. Examples (from the project root):

    docker compose exec -it backend python -m app.cli create-superadmin --email you@example.com
    docker compose exec backend python -m app.cli import-source --file /data/sources/x.pdf \\
        --title "Grade 6 English curriculum design" --publisher "Kenya Institute of Curriculum Development"
"""
import argparse
import getpass
import uuid
from pathlib import Path

from sqlalchemy import select

from app.core.passwords import validate_password_strength
from app.db.session import SessionLocal
from app.models import CurriculumSource, CurriculumSourcePage
from app.services.admin import bootstrap_super_admin
from app.services.auth import get_user_by_email
from app.services import curriculum as curriculum_service
from app.services.importer import import_pdf, propose_from_source


def create_superadmin(email: str, name: str) -> int:
    with SessionLocal() as db:
        existing = get_user_by_email(db, email)
        password = None
        if existing is None:
            password = getpass.getpass("Password: ")
            if password != getpass.getpass("Repeat password: "):
                print("Passwords do not match.")
                return 1
            try:
                validate_password_strength(password, email)
            except ValueError as exc:
                print(exc)
                return 1
        bootstrap_super_admin(db, email=email, password=password, display_name=name)
    if existing is None:
        print(f"Created super administrator {email}.")
    else:
        print(f"Existing account {email} now has the super_admin role.")
    return 0


def import_source(file: str, title: str, publisher: str, edition: str | None) -> int:
    path = Path(file)
    if not path.is_file():
        print(f"File not found: {file}")
        return 1
    try:
        with SessionLocal() as db:
            result = import_pdf(
                db, data=path.read_bytes(), filename=path.name, title=title,
                publisher=publisher, edition_label=edition,
            )
            source = result.source
            print(("Registered" if result.created else "Already registered") + f": {source.title}")
            print(f"Source id: {source.id}")
            print(f"Pages stored: {result.pages_total} ({result.pages_added} new)")
            print(f"Licence status: {source.license_status}")
    except ValueError as exc:
        print(exc)
        return 1
    print("Publishing content from this source stays blocked until its licence status is 'granted'.")
    return 0


def create_curriculum(code: str, name: str, country: str) -> int:
    try:
        with SessionLocal() as db:
            row = curriculum_service.create_curriculum(db, None, code, name, country)
            print(f"Created curriculum {row.code}  id={row.id}")
    except curriculum_service.Conflict as exc:
        print(exc.message)
        return 1
    return 0


def create_version(code: str, label: str) -> int:
    from app.models import Curriculum

    try:
        with SessionLocal() as db:
            cur = db.scalar(select(Curriculum).where(Curriculum.code == code))
            if cur is None:
                print(f"No curriculum with code '{code}'. Create it first with create-curriculum.")
                return 1
            row = curriculum_service.create_version(db, None, cur.id, label)
            print(f"Created draft version '{row.label}'  id={row.id}")
    except curriculum_service.Conflict as exc:
        print(exc.message)
        return 1
    return 0


def list_sources() -> int:
    with SessionLocal() as db:
        for s in db.scalars(select(CurriculumSource).order_by(CurriculumSource.title)):
            print(f"{s.id}  pages={s.page_count}  licence={s.license_status}  {s.title}")
    return 0


def parse_uuid(value: str, what: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value.strip())
    except ValueError:
        print(f"'{value}' is not a valid {what}. Copy the long id (like 3f2b9c1e-...) from list-sources.")
        return None


def propose(source: str, version: str, grade_level: int, grade_name: str | None, area: str, dry_run: bool) -> int:
    source_id, version_id = parse_uuid(source, "source id"), parse_uuid(version, "version id")
    if source_id is None or version_id is None:
        return 1
    try:
        with SessionLocal() as db:
            result = propose_from_source(
                db, source_id=source_id, version_id=version_id, grade_level=grade_level,
                grade_name=grade_name or f"Grade {grade_level}", area_name=area, dry_run=dry_run,
            )
    except curriculum_service.NotFound:
        print("Source or version not found.")
        return 1
    except curriculum_service.Conflict as exc:
        print(exc.message)
        return 1
    print(f"Recognised {result.strands} strands, {result.sub_strands} sub-strands, {result.outcomes} learning outcomes.")
    print(f"Items needing a human check: {len(result.warnings)}")
    for warning in result.warnings[:60]:
        print("  -", warning)
    if dry_run:
        print("Dry run: nothing was written.")
    else:
        print(f"Created draft learning area {result.learning_area_id}. Every record is in 'draft' review status.")
    return 0


def show_page(source_id: str, page: int) -> int:
    parsed = parse_uuid(source_id, "source id")
    if parsed is None:
        return 1
    with SessionLocal() as db:
        row = db.scalar(
            select(CurriculumSourcePage).where(
                CurriculumSourcePage.source_id == parsed,
                CurriculumSourcePage.pdf_page == page,
            )
        )
        if row is None:
            print("No such page.")
            return 1
        print(f"--- pdf page {row.pdf_page}, printed page {row.printed_page or '(none detected)'} ---")
        print(row.text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-superadmin", help="Create or promote a super administrator")
    p.add_argument("--email", required=True)
    p.add_argument("--name", default="Administrator")

    p = sub.add_parser("import-source", help="Register a source PDF and store its page text")
    p.add_argument("--file", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--publisher", required=True)
    p.add_argument("--edition")

    sub.add_parser("list-sources", help="List registered source documents")

    p = sub.add_parser("show-page", help="Print the stored text of one page")
    p.add_argument("--source", required=True)
    p.add_argument("--page", type=int, required=True)

    p = sub.add_parser("create-curriculum", help="Create a curriculum (for example kenya-cbe)")
    p.add_argument("--code", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--country", default="KE")

    p = sub.add_parser("create-version", help="Create a draft version of a curriculum")
    p.add_argument("--curriculum", required=True, help="curriculum code")
    p.add_argument("--label", required=True)

    p = sub.add_parser("propose", help="Create DRAFT curriculum records from a stored source")
    p.add_argument("--source", required=True)
    p.add_argument("--version", required=True, help="id of a draft curriculum version")
    p.add_argument("--grade-level", type=int, required=True)
    p.add_argument("--grade-name")
    p.add_argument("--area", required=True, help="learning area name, e.g. Mathematics")
    p.add_argument("--dry-run", action="store_true", help="parse and report only; write nothing")

    args = parser.parse_args(argv)
    if args.command == "create-curriculum":
        return create_curriculum(args.code, args.name, args.country)
    if args.command == "create-version":
        return create_version(args.curriculum, args.label)
    if args.command == "propose":
        return propose(args.source, args.version, args.grade_level, args.grade_name, args.area, args.dry_run)
    if args.command == "create-superadmin":
        return create_superadmin(args.email, args.name)
    if args.command == "import-source":
        return import_source(args.file, args.title, args.publisher, args.edition)
    if args.command == "list-sources":
        return list_sources()
    return show_page(args.source, args.page)


if __name__ == "__main__":
    raise SystemExit(main())
