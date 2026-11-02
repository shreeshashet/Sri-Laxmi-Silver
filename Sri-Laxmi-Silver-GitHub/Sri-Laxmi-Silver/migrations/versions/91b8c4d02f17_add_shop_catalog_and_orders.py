"""add shop catalog and orders

Revision ID: 91b8c4d02f17
Revises: 5cf5fe27dae0
Create Date: 2026-10-20 10:48:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "91b8c4d02f17"
down_revision = "5cf5fe27dae0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shop_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=1000), nullable=False),
        sa.Column("price_paise", sa.Integer(), nullable=True),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "price_paise IS NULL OR price_paise > 0",
            name="ck_shop_products_positive_price",
        ),
        sa.CheckConstraint(
            "stock_quantity >= 0",
            name="ck_shop_products_nonnegative_stock",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("shop_products", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_shop_products_category"),
            ["category"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_shop_products_is_published"),
            ["is_published"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_shop_products_slug"),
            ["slug"],
            unique=True,
        )

    op.create_table(
        "shop_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("customer_phone", sa.String(length=30), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("delivery_address", sa.Text(), nullable=False),
        sa.Column("delivery_postal_code", sa.String(length=10), nullable=False),
        sa.Column("subtotal_paise", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "subtotal_paise >= 0",
            name="ck_shop_orders_nonnegative_subtotal",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("shop_orders", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_shop_orders_order_number"),
            ["order_number"],
            unique=True,
        )

    op.create_table(
        "shop_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_name", sa.String(length=160), nullable=False),
        sa.Column("unit_price_paise", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["shop_orders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["shop_products.id"],
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_shop_order_items_positive_quantity",
        ),
        sa.CheckConstraint(
            "unit_price_paise > 0",
            name="ck_shop_order_items_positive_price",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("shop_order_items", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_shop_order_items_order_id"),
            ["order_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("shop_order_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_shop_order_items_order_id"))
    op.drop_table("shop_order_items")

    with op.batch_alter_table("shop_orders", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_shop_orders_order_number"))
    op.drop_table("shop_orders")

    with op.batch_alter_table("shop_products", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_shop_products_slug"))
        batch_op.drop_index(batch_op.f("ix_shop_products_is_published"))
        batch_op.drop_index(batch_op.f("ix_shop_products_category"))
    op.drop_table("shop_products")
