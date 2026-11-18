"""curriculum engine: versions, grades, areas, units, strands, sub-strands, content, sources

Revision ID: 0005
Revises: 0004
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

COMPETENCIES = [
    ("communication_collaboration", "Communication and Collaboration"),
    ("critical_thinking", "Critical Thinking and Problem Solving"),
    ("creativity_imagination", "Creativity and Imagination"),
    ("citizenship", "Citizenship"),
    ("digital_literacy", "Digital Literacy"),
    ("learning_to_learn", "Learning to Learn"),
    ("self_efficacy", "Self-Efficacy"),
]


def ts():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def review(table):
    return [
        sa.Column("review_status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), nullable=True),
        sa.Column("source_page_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["reviewed_by_id"], ["users.id"], name=f"fk_{table}_reviewed_by_id_users", ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["source_page_id"],
            ["curriculum_source_pages.id"],
            name=f"fk_{table}_source_page_id_curriculum_source_pages",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "review_status IN ('draft','in_review','approved','rejected')",
            name=f"ck_{table}_review_status_valid",
        ),
    ]


def pk(table):
    return sa.PrimaryKeyConstraint("id", name=f"pk_{table}")


def fk(table, col, ref_table, ondelete="CASCADE"):
    return sa.ForeignKeyConstraint(
        [col], [f"{ref_table}.id"], name=f"fk_{table}_{col}_{ref_table}", ondelete=ondelete
    )


def upgrade() -> None:
    op.create_table(
        "curricula",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        *ts(),
        pk("curricula"),
        sa.UniqueConstraint("code", name="uq_curricula_code"),
    )

    op.create_table(
        "curriculum_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("curriculum_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        *ts(),
        pk("curriculum_versions"),
        fk("curriculum_versions", "curriculum_id", "curricula"),
        sa.UniqueConstraint("curriculum_id", "label", name="uq_curriculum_versions_curriculum_label"),
        sa.CheckConstraint("status IN ('draft','published','archived')", name="ck_curriculum_versions_status_valid"),
    )
    op.create_index(
        "uq_curriculum_versions_one_published",
        "curriculum_versions",
        ["curriculum_id"],
        unique=True,
        postgresql_where=sa.text("status = 'published'"),
    )

    op.create_table(
        "curriculum_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("publisher", sa.String(200), nullable=False),
        sa.Column("edition_label", sa.String(100), nullable=True),
        sa.Column("original_filename", sa.String(300), nullable=True),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("license_status", sa.String(20), server_default="not_requested", nullable=False),
        sa.Column("license_notes", sa.Text(), nullable=True),
        *ts(),
        pk("curriculum_sources"),
        sa.UniqueConstraint("file_sha256", name="uq_curriculum_sources_file_sha256"),
        sa.CheckConstraint(
            "license_status IN ('not_requested','requested','granted','denied')",
            name="ck_curriculum_sources_license_status_valid",
        ),
    )

    op.create_table(
        "curriculum_source_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("pdf_page", sa.Integer(), nullable=False),
        sa.Column("printed_page", sa.String(20), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        pk("curriculum_source_pages"),
        fk("curriculum_source_pages", "source_id", "curriculum_sources"),
        sa.UniqueConstraint("source_id", "pdf_page", name="uq_source_pages_source_pdf_page"),
    )

    core = op.create_table(
        "core_competencies",
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_core_competencies"),
    )
    op.bulk_insert(core, [{"code": c, "name": n} for c, n in COMPETENCIES])

    op.create_table(
        "curriculum_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        pk("curriculum_values"),
    )
    op.create_index("uq_curriculum_values_name_lower", "curriculum_values", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "pertinent_contemporary_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        pk("pertinent_contemporary_issues"),
    )
    op.create_index("uq_pcis_name_lower", "pertinent_contemporary_issues", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "grades",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("curriculum_version_id", sa.Uuid(), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        *ts(),
        pk("grades"),
        fk("grades", "curriculum_version_id", "curriculum_versions"),
        sa.UniqueConstraint("curriculum_version_id", "level", name="uq_grades_version_level"),
        sa.CheckConstraint("level BETWEEN 1 AND 12", name="ck_grades_level_range"),
    )
    op.create_index("ix_grades_curriculum_version_id", "grades", ["curriculum_version_id"])

    op.create_table(
        "learning_areas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("grade_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *review("learning_areas"),
        *ts(),
        pk("learning_areas"),
        fk("learning_areas", "grade_id", "grades"),
    )
    op.create_index("ix_learning_areas_grade_id", "learning_areas", ["grade_id"])
    op.create_index(
        "uq_learning_areas_grade_name_active",
        "learning_areas",
        ["grade_id", sa.text("lower(name)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )

    op.create_table(
        "units",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("learning_area_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *review("units"),
        *ts(),
        pk("units"),
        fk("units", "learning_area_id", "learning_areas"),
    )
    op.create_index("ix_units_learning_area_id", "units", ["learning_area_id"])

    op.create_table(
        "strands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("learning_area_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=True),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *review("strands"),
        *ts(),
        pk("strands"),
        fk("strands", "learning_area_id", "learning_areas"),
        fk("strands", "unit_id", "units", ondelete="SET NULL"),
    )
    op.create_index("ix_strands_learning_area_id", "strands", ["learning_area_id"])

    op.create_table(
        "sub_strands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("strand_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("suggested_lessons", sa.SmallInteger(), nullable=True),
        sa.Column("link_to_other_areas", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *review("sub_strands"),
        *ts(),
        pk("sub_strands"),
        fk("sub_strands", "strand_id", "strands"),
        sa.UniqueConstraint("strand_id", "number", name="uq_sub_strands_strand_number"),
    )
    op.create_index("ix_sub_strands_strand_id", "sub_strands", ["strand_id"])

    def child(table, *cols):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("sub_strand_id", sa.Uuid(), nullable=False),
            *cols,
            sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
            pk(table),
            fk(table, "sub_strand_id", "sub_strands"),
        )
        op.create_index(f"ix_{table}_sub_strand_id", table, ["sub_strand_id"])

    child("topics", sa.Column("name", sa.String(300), nullable=False))
    child("learning_outcomes", sa.Column("code", sa.String(10), nullable=True), sa.Column("text", sa.Text(), nullable=False))
    child("learning_experiences", sa.Column("text", sa.Text(), nullable=False))
    child("key_inquiry_questions", sa.Column("text", sa.Text(), nullable=False))

    op.create_table(
        "sub_strand_competencies",
        sa.Column("sub_strand_id", sa.Uuid(), nullable=False),
        sa.Column("competency_code", sa.String(40), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("sub_strand_id", "competency_code", name="pk_sub_strand_competencies"),
        fk("sub_strand_competencies", "sub_strand_id", "sub_strands"),
        sa.ForeignKeyConstraint(
            ["competency_code"], ["core_competencies.code"],
            name="fk_sub_strand_competencies_competency_code_core_competencies",
        ),
    )
    op.create_table(
        "sub_strand_values",
        sa.Column("sub_strand_id", sa.Uuid(), nullable=False),
        sa.Column("value_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("sub_strand_id", "value_id", name="pk_sub_strand_values"),
        fk("sub_strand_values", "sub_strand_id", "sub_strands"),
        sa.ForeignKeyConstraint(
            ["value_id"], ["curriculum_values.id"], name="fk_sub_strand_values_value_id_curriculum_values"
        ),
    )
    op.create_table(
        "sub_strand_pcis",
        sa.Column("sub_strand_id", sa.Uuid(), nullable=False),
        sa.Column("pci_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("sub_strand_id", "pci_id", name="pk_sub_strand_pcis"),
        fk("sub_strand_pcis", "sub_strand_id", "sub_strands"),
        sa.ForeignKeyConstraint(
            ["pci_id"], ["pertinent_contemporary_issues.id"],
            name="fk_sub_strand_pcis_pci_id_pertinent_contemporary_issues",
        ),
    )

    op.create_table(
        "rubric_indicators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("strand_id", sa.Uuid(), nullable=False),
        sa.Column("indicator", sa.Text(), nullable=False),
        sa.Column("exceeds", sa.Text(), nullable=False),
        sa.Column("meets", sa.Text(), nullable=False),
        sa.Column("approaches", sa.Text(), nullable=False),
        sa.Column("below", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        pk("rubric_indicators"),
        fk("rubric_indicators", "strand_id", "strands"),
    )
    op.create_index("ix_rubric_indicators_strand_id", "rubric_indicators", ["strand_id"])


def downgrade() -> None:
    for table in (
        "rubric_indicators", "sub_strand_pcis", "sub_strand_values", "sub_strand_competencies",
        "key_inquiry_questions", "learning_experiences", "learning_outcomes", "topics",
        "sub_strands", "strands", "units", "learning_areas", "grades",
        "pertinent_contemporary_issues", "curriculum_values", "core_competencies",
        "curriculum_source_pages", "curriculum_sources", "curriculum_versions", "curricula",
    ):
        op.drop_table(table)
