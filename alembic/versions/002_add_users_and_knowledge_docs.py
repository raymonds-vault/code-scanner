"""add users, knowledge_documents, and user_id on scans

Revision ID: 002
Revises: 001
Create Date: 2026-05-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("google_id", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("picture", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("source", sa.String(length=256), nullable=False),
        sa.Column("category", sa.String(length=256), nullable=False),
        sa.Column("doc_version", sa.String(length=64), nullable=False),
        sa.Column("namespace", sa.String(length=128), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("scans", sa.Column("user_id", sa.String(length=36), nullable=True))


def downgrade() -> None:
    op.drop_column("scans", "user_id")
    op.drop_table("knowledge_documents")
    op.drop_table("users")
