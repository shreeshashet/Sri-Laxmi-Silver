"""track stock reserved by confirmed shop orders

Revision ID: 72d3c1a8095e
Revises: 91b8c4d02f17
Create Date: 2026-10-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "72d3c1a8095e"
down_revision = "91b8c4d02f17"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "shop_orders",
        sa.Column(
            "stock_reserved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column("shop_orders", "stock_reserved")
