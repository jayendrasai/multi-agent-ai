"""Add users, sessions, and task ownership.

Revision ID: 9f3b4e1a2c7d
Revises: 4b8ce7e3fd93
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9f3b4e1a2c7d"
down_revision: Union[str, Sequence[str], None] = "4b8ce7e3fd93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("workflow_interest", sa.String(length=50), nullable=True),
        sa.Column("team_size", sa.String(length=30), nullable=True),
        sa.Column("experience_level", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=False)
    op.create_index("idx_users_username", "users", ["username"], unique=False)

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_digest"),
    )
    op.create_index("idx_sessions_user", "sessions", ["user_id"], unique=False)
    op.create_index("idx_sessions_active", "sessions", ["token_digest", "expires_at", "revoked_at"], unique=False)

    op.add_column("task_runs", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_task_runs_user_id", "task_runs", "users", ["user_id"], ["id"], ondelete="SET NULL")
    op.create_index("idx_task_runs_user_created", "task_runs", ["user_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_task_runs_user_created", table_name="task_runs")
    op.drop_constraint("fk_task_runs_user_id", "task_runs", type_="foreignkey")
    op.drop_column("task_runs", "user_id")
    op.drop_index("idx_sessions_active", table_name="sessions")
    op.drop_index("idx_sessions_user", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
