"""add named shop collections

Revision ID: 3ac42df9184e
Revises: eb3975ad75ee
Create Date: 2026-11-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "3ac42df9184e"
down_revision = "eb3975ad75ee"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shop_collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column(
            "description",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("shop_collections") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_shop_collections_is_published"),
            ["is_published"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_shop_collections_slug"),
            ["slug"],
            unique=True,
        )

    with op.batch_alter_table("shop_products") as batch_op:
        batch_op.add_column(sa.Column("collection_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_shop_products_collection_id"),
            ["collection_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_shop_products_collection_id_shop_collections",
            "shop_collections",
            ["collection_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("shop_products") as batch_op:
        batch_op.drop_constraint(
            "fk_shop_products_collection_id_shop_collections",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_shop_products_collection_id"))
        batch_op.drop_column("collection_id")

    with op.batch_alter_table("shop_collections") as batch_op:
        batch_op.drop_index(batch_op.f("ix_shop_collections_slug"))
        batch_op.drop_index(batch_op.f("ix_shop_collections_is_published"))
    op.drop_table("shop_collections")
