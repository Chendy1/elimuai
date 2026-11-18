"""Operator commands. Example (from the project root):

    docker compose exec -it backend python -m app.cli create-superadmin --email you@example.com
"""
import argparse
import getpass

from app.core.passwords import validate_password_strength
from app.db.session import SessionLocal
from app.services.admin import bootstrap_super_admin
from app.services.auth import get_user_by_email


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("create-superadmin", help="Create or promote a super administrator")
    p.add_argument("--email", required=True)
    p.add_argument("--name", default="Administrator")
    args = parser.parse_args(argv)
    return create_superadmin(args.email, args.name)


if __name__ == "__main__":
    raise SystemExit(main())
