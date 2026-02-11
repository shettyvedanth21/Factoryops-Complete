from alembic import op
import sqlalchemy as sa


revision = "<put your new revision id here>"
down_revision = "d74fc8909d3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "analytics_jobs",
        "created_at",
        server_default=sa.text("now()"),
        existing_nullable=False,
    )

    op.alter_column(
        "analytics_jobs",
        "updated_at",
        server_default=sa.text("now()"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "analytics_jobs",
        "created_at",
        server_default=None,
        existing_nullable=False,
    )

    op.alter_column(
        "analytics_jobs",
        "updated_at",
        server_default=None,
        existing_nullable=False,
    )