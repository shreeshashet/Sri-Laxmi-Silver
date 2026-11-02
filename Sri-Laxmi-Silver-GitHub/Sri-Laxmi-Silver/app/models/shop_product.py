from datetime import datetime, timezone

from ..extensions import db


class ShopProduct(db.Model):
    __tablename__ = "shop_products"
    __table_args__ = (
        db.CheckConstraint(
            "price_paise IS NULL OR price_paise > 0",
            name="ck_shop_products_positive_price",
        ),
        db.CheckConstraint(
            "stock_quantity >= 0",
            name="ck_shop_products_nonnegative_stock",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("shop_collections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description = db.Column(db.Text, nullable=False, default="")
    image_url = db.Column(db.String(1000), nullable=False)
    price_paise = db.Column(db.Integer, nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_demo = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    collection = db.relationship("ShopCollection", backref="products")


class ShopCollection(db.Model):
    __tablename__ = "shop_collections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False, default="")
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ShopOrder(db.Model):
    __tablename__ = "shop_orders"
    __table_args__ = (
        db.CheckConstraint(
            "subtotal_paise >= 0",
            name="ck_shop_orders_nonnegative_subtotal",
        ),
        db.CheckConstraint(
            "discount_paise >= 0 AND discount_paise <= subtotal_paise",
            name="ck_shop_orders_valid_discount",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    customer_email = db.Column(db.String(255), nullable=True)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_postal_code = db.Column(db.String(10), nullable=False)
    subtotal_paise = db.Column(db.Integer, nullable=False)
    discount_paise = db.Column(db.Integer, nullable=False, default=0)
    coupon_code = db.Column(db.String(40), nullable=True)
    status = db.Column(db.String(40), nullable=False, default="awaiting_whatsapp")
    stock_reserved = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_shop_orders_user_id_users"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items = db.relationship(
        "ShopOrderItem",
        backref="order",
        lazy=True,
        cascade="all, delete-orphan",
    )
    customer = db.relationship("User", backref="shop_orders")

    @property
    def total_paise(self):
        return max(0, self.subtotal_paise - self.discount_paise)


class ShopOrderItem(db.Model):
    __tablename__ = "shop_order_items"
    __table_args__ = (
        db.CheckConstraint(
            "quantity > 0",
            name="ck_shop_order_items_positive_quantity",
        ),
        db.CheckConstraint(
            "unit_price_paise > 0",
            name="ck_shop_order_items_positive_price",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("shop_orders.id"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("shop_products.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_name = db.Column(db.String(160), nullable=False)
    unit_price_paise = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


class ShopCoupon(db.Model):
    __tablename__ = "shop_coupons"
    __table_args__ = (
        db.CheckConstraint(
            "discount_value > 0",
            name="ck_shop_coupons_positive_discount",
        ),
        db.CheckConstraint(
            "minimum_subtotal_paise >= 0",
            name="ck_shop_coupons_nonnegative_minimum",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    discount_type = db.Column(db.String(10), nullable=False)
    discount_value = db.Column(db.Integer, nullable=False)
    minimum_subtotal_paise = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)


class ShopReview(db.Model):
    __tablename__ = "shop_reviews"
    __table_args__ = (
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_shop_reviews_rating_range",
        ),
        db.UniqueConstraint("order_item_id", name="uq_shop_reviews_order_item"),
    )

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("shop_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_item_id = db.Column(
        db.Integer,
        db.ForeignKey("shop_order_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product = db.relationship("ShopProduct", backref="reviews")
    customer = db.relationship("User", backref="shop_reviews")
    order_item = db.relationship("ShopOrderItem", backref="review")
