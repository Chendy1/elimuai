"""roles, user_roles (backfilled with guardian), audit_logs

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

ROLES = [
    ("student", "A learner using the platform with their own account (later phase)."),
    ("guardian", "A parent or guardian who manages learner profiles and consent."),
    ("teacher", "A teacher managing approved classes and assessments."),
    ("curriculum_admin", "Manages curriculum structure and publishing."),
    ("content_reviewer", "Reviews lessons, AI-generated content and questions."),
    ("institutional_partner", "Sees aggregate, anonymised programme reports only."),
    ("super_admin", "Full platform administration."),
]


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("name", name="pk_roles"),
    )
    op.bulk_insert(roles, [{"name": n, "description": d} for n, d in ROLES])

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_name", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "role_name", name="pk_user_roles"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_name"], ["roles.name"], name="fk_user_roles_role_name_roles"),
    )
    # Every account created before roles existed is a guardian.
    op.execute("INSERT INTO user_roles (user_id, role_name) SELECT id, 'guardian' FROM users")

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=True),
        sa.Column("target_id", sa.String(64), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name="fk_audit_logs_actor_user_id_users", ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("user_roles")
    op.drop_table("roles")
