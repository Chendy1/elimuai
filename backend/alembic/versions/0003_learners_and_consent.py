"""learners and consent_records

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learners",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("grade", sa.SmallInteger(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_learners"),
        sa.ForeignKeyConstraint(["guardian_id"], ["users.id"], name="fk_learners_guardian_id_users", ondelete="CASCADE"),
        sa.CheckConstraint("grade BETWEEN 4 AND 9", name="ck_learners_grade_range"),
    )
    op.create_index("ix_learners_guardian_id", "learners", ["guardian_id"])
    op.create_index(
        "uq_learners_guardian_nickname_active",
        "learners",
        ["guardian_id", sa.text("lower(nickname)")],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "consent_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("learner_id", sa.Uuid(), nullable=False),
        sa.Column("guardian_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(50), nullable=False),
        sa.Column("notice_version", sa.String(32), nullable=False),
        sa.Column("notice_sha256", sa.String(64), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_consent_records"),
        sa.ForeignKeyConstraint(["learner_id"], ["learners.id"], name="fk_consent_records_learner_id_learners", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guardian_id"], ["users.id"], name="fk_consent_records_guardian_id_users", ondelete="CASCADE"),
    )
    op.create_index("ix_consent_records_learner_id", "consent_records", ["learner_id"])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("learners")
