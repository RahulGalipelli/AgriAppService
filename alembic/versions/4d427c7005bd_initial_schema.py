"""initial_schema

Revision ID: 4d427c7005bd
Revises:
Create Date: 2025-12-25 11:41:33.164388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "4d427c7005bd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema. Order matters: users before carts/orders; plant_scans before scan_*."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("phone", sa.String(length=15), nullable=True),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column("language", sa.String(length=10), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    if "user_sessions" not in existing_tables:
        op.create_table(
            "user_sessions",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token"),
        )

    if "products" not in existing_tables:
        op.create_table(
            "products",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "plant_scans" not in existing_tables:
        op.create_table(
            "plant_scans",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("image_filename", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "carts" not in existing_tables:
        op.create_table(
            "carts",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "orders" not in existing_tables:
        op.create_table(
            "orders",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=True),
            sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "product_images" not in existing_tables:
        op.create_table(
            "product_images",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("product_id", sa.UUID(), nullable=True),
            sa.Column("image_url", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "product_inventory" not in existing_tables:
        op.create_table(
            "product_inventory",
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("product_id"),
        )

    if "scan_results" not in existing_tables:
        op.create_table(
            "scan_results",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("scan_id", sa.UUID(), nullable=False),
            sa.Column("result_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["scan_id"], ["plant_scans.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "scan_product_recommendations" not in existing_tables:
        op.create_table(
            "scan_product_recommendations",
            sa.Column("scan_id", sa.UUID(), nullable=False),
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("rank", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["scan_id"], ["plant_scans.id"]),
            sa.PrimaryKeyConstraint("scan_id", "product_id"),
        )

    if "user_roles" not in existing_tables:
        op.create_table(
            "user_roles",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=True),
            sa.Column("role", sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "cart_items" not in existing_tables:
        op.create_table(
            "cart_items",
            sa.Column("cart_id", sa.UUID(), nullable=False),
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("cart_id", "product_id"),
        )

    if "order_events" not in existing_tables:
        op.create_table(
            "order_events",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("order_id", sa.UUID(), nullable=True),
            sa.Column("event", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "order_items" not in existing_tables:
        op.create_table(
            "order_items",
            sa.Column("order_id", sa.UUID(), nullable=False),
            sa.Column("product_id", sa.UUID(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=True),
            sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.PrimaryKeyConstraint("order_id", "product_id"),
        )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("order_events")
    op.drop_table("cart_items")
    op.drop_table("user_roles")
    op.drop_table("scan_product_recommendations")
    op.drop_table("scan_results")
    op.drop_table("product_inventory")
    op.drop_table("product_images")
    op.drop_table("orders")
    op.drop_table("carts")
    op.drop_table("plant_scans")
    op.drop_table("products")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")