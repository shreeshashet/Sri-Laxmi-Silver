import hmac
import re
import secrets
from decimal import Decimal, InvalidOperation
from functools import wraps
from urllib.parse import quote

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from . import shop_bp
from ..extensions import db
from ..models import (
    ShopCollection,
    ShopCoupon,
    ShopOrder,
    ShopOrderItem,
    ShopProduct,
    ShopReview,
)
from ..auth.forms import validate_email


ORDER_STATUSES = {
    "awaiting_whatsapp": "Awaiting WhatsApp confirmation",
    "confirmed": "Confirmed",
    "fulfilled": "Fulfilled",
    "cancelled": "Cancelled",
}
ORDER_TRANSITIONS = {
    "awaiting_whatsapp": {"awaiting_whatsapp", "confirmed", "cancelled"},
    "confirmed": {"confirmed", "fulfilled", "cancelled"},
    "fulfilled": {"fulfilled"},
    "cancelled": {"cancelled"},
}
SHOP_CATEGORIES = ("Jewellery", "Keepsakes")
DEMO_PRODUCTS = (
    (
        "Silver earrings",
        "Jewellery",
        "A sample listing for the Sri Laxmi Silver collection. Confirm current designs and pricing with the store.",
        "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=720&q=80",
    ),
    (
        "Silver necklaces",
        "Jewellery",
        "A sample listing for the Sri Laxmi Silver collection. Confirm current designs and pricing with the store.",
        "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=720&q=80",
    ),
    (
        "Silver anklets",
        "Jewellery",
        "A sample listing for the Sri Laxmi Silver collection. Confirm current designs and pricing with the store.",
        "https://images.unsplash.com/photo-1617038220319-276d3cfab638?auto=format&fit=crop&w=720&q=80",
    ),
    (
        "Silver keepsakes",
        "Keepsakes",
        "A sample listing for the Sri Laxmi Silver collection. Confirm current designs and pricing with the store.",
        "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=720&q=80",
    ),
)


def _cart():
    cart = session.get("shop_cart", {})
    if not isinstance(cart, dict):
        return {}
    return {
        str(product_id): quantity
        for product_id, quantity in cart.items()
        if str(product_id).isdigit()
        and isinstance(quantity, int)
        and 1 <= quantity <= 100000
    }


def _csrf_token():
    token = session.get("_shop_csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["_shop_csrf_token"] = token
    return token


def _valid_csrf():
    expected = session.get("_shop_csrf_token", "")
    provided = request.form.get("csrf_token", "")
    return (
        isinstance(expected, str)
        and isinstance(provided, str)
        and bool(expected)
        and hmac.compare_digest(expected, provided)
    )


def _require_csrf():
    if not _valid_csrf():
        abort(400, description="Your session expired. Please try again.")


def _is_shop_admin():
    allowed_emails = current_app.config["SHOP_ADMIN_EMAILS"]
    return (
        current_user.is_authenticated
        and current_user.email.lower() in allowed_emails
    )


def _admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        if not _is_shop_admin():
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _cart_products():
    cart = _cart()
    product_ids = [int(value) for value in cart if str(value).isdigit()]
    if not product_ids:
        return [], 0

    products = ShopProduct.query.filter(
        ShopProduct.id.in_(product_ids),
        ShopProduct.is_published.is_(True),
    ).all()
    rows = []
    subtotal = 0
    for product in products:
        quantity = int(cart.get(str(product.id), 0))
        if quantity < 1:
            continue
        if product.is_demo or product.price_paise is None or product.price_paise <= 0:
            continue
        line_total = product.price_paise * quantity
        rows.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total": line_total,
            }
        )
        subtotal += line_total
    return rows, subtotal


def _remove_unavailable_items():
    cart = _cart()
    if not cart:
        return
    products = ShopProduct.query.filter(
        ShopProduct.id.in_([int(product_id) for product_id in cart]),
        ShopProduct.is_published.is_(True),
        ShopProduct.is_demo.is_(False),
        ShopProduct.price_paise.is_not(None),
        ShopProduct.price_paise > 0,
    ).all()
    available_ids = {str(product.id) for product in products}
    updated_cart = {
        product_id: quantity
        for product_id, quantity in cart.items()
        if product_id in available_ids
    }
    if updated_cart != cart:
        session["shop_cart"] = updated_cart
        flash("Some items are no longer available and were removed from your bag.", "error")


def _parse_rupees(value):
    try:
        amount = Decimal(value.strip())
        if (
            not amount.is_finite()
            or amount <= 0
            or amount > Decimal("10000000")
            or amount != amount.quantize(Decimal("0.01"))
        ):
            return None
    except (InvalidOperation, AttributeError):
        return None
    return int(amount * 100)


def _parse_nonnegative_rupees(value):
    try:
        amount = Decimal(value.strip())
        if (
            not amount.is_finite()
            or amount < 0
            or amount > Decimal("10000000")
            or amount != amount.quantize(Decimal("0.01"))
        ):
            return None
    except (InvalidOperation, AttributeError):
        return None
    return int(amount * 100)


def _coupon_discount(coupon, subtotal):
    if coupon.discount_type == "percent":
        return min(subtotal, subtotal * coupon.discount_value // 100)
    return min(subtotal, coupon.discount_value)


def _active_cart_coupon(subtotal):
    code = session.get("shop_coupon_code")
    if not isinstance(code, str) or not code:
        return None, 0
    coupon = ShopCoupon.query.filter_by(code=code, is_active=True).first()
    if coupon is None:
        session.pop("shop_coupon_code", None)
        flash("The applied coupon is no longer active.", "error")
        return None, 0
    if subtotal < coupon.minimum_subtotal_paise:
        session.pop("shop_coupon_code", None)
        flash("Your order no longer meets the minimum for the applied coupon.", "error")
        return None, 0
    return coupon, _coupon_discount(coupon, subtotal)


def _render_checkout(
    rows,
    subtotal,
    status=200,
    customer_name=None,
    customer_email=None,
):
    coupon, discount = _active_cart_coupon(subtotal)
    response = render_template(
        "shop/checkout.html",
        rows=rows,
        subtotal=subtotal,
        coupon=coupon,
        discount=discount,
        customer_name=(
            customer_name if customer_name is not None else current_user.name or ""
        ),
        customer_email=(
            customer_email
            if customer_email is not None
            else current_user.email
        ),
    )
    return response, status


def seed_demo_catalog():
    if ShopProduct.query.filter_by(is_demo=True).first():
        return 0
    for name, category, description, image_url in DEMO_PRODUCTS:
        db.session.add(
            ShopProduct(
                name=name,
                slug=_new_slug(name),
                category=category,
                description=description,
                image_url=image_url,
                price_paise=None,
                stock_quantity=0,
                is_published=True,
                is_demo=True,
            )
        )
    db.session.commit()
    return len(DEMO_PRODUCTS)


def _new_slug(value, exclude_id=None):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:150]
    base_slug = slug or "product"
    candidate = base_slug
    suffix = 2
    existing = ShopProduct.query.filter_by(slug=candidate).first()
    while existing and existing.id != exclude_id:
        candidate = f"{base_slug[:170]}-{suffix}"
        suffix += 1
        existing = ShopProduct.query.filter_by(slug=candidate).first()
    return candidate


def _new_collection_slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:100]
    base_slug = slug or "collection"
    candidate = base_slug
    suffix = 2
    existing = ShopCollection.query.filter_by(slug=candidate).first()
    while existing:
        candidate = f"{base_slug[:110]}-{suffix}"
        suffix += 1
        existing = ShopCollection.query.filter_by(slug=candidate).first()
    return candidate


def _product_form_values():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    raw_collection_id = request.form.get("collection_id", "").strip()
    price_paise = _parse_rupees(request.form.get("price", ""))
    try:
        stock_quantity = int(request.form.get("stock_quantity", ""))
    except ValueError:
        stock_quantity = -1

    valid_image = image_url.startswith(("https://", "/static/"))
    if not name or len(name) > 160:
        return None, "Enter a product name up to 160 characters."
    if category not in SHOP_CATEGORIES:
        return None, "Choose a valid product category."
    try:
        collection_id = int(raw_collection_id) if raw_collection_id else None
    except ValueError:
        return None, "Choose a valid collection."
    if collection_id is not None and db.session.get(ShopCollection, collection_id) is None:
        return None, "Choose a valid collection."
    if not valid_image or len(image_url) > 1000:
        return None, "Use an HTTPS image URL or a local /static/ image path."
    if price_paise is None:
        return None, "Enter a positive product price in rupees."
    if not 0 <= stock_quantity <= 100000:
        return None, "Stock must be a number between 0 and 100,000."
    return {
        "name": name,
        "category": category,
        "collection_id": collection_id,
        "description": description[:5000],
        "image_url": image_url,
        "price_paise": price_paise,
        "stock_quantity": stock_quantity,
        "is_demo": request.form.get("is_demo") == "on",
        "is_published": request.form.get("is_published") == "on",
    }, None


@shop_bp.app_context_processor
def inject_shop_context():
    cart_count = sum(_cart().values())
    return {
        "shop_csrf_token": _csrf_token,
        "shop_cart_count": cart_count,
        "is_shop_admin": _is_shop_admin,
    }


@shop_bp.route("/about")
def about():
    return render_template("shop/about.html")


@shop_bp.route("/contact")
def contact():
    return render_template("shop/contact.html")


@shop_bp.route("/help")
def help_page():
    return render_template("shop/help.html")


@shop_bp.route("/privacy")
def privacy():
    return render_template("shop/privacy.html")


@shop_bp.route("/collections")
def collections():
    active_collections = (
        ShopCollection.query.filter_by(is_published=True)
        .order_by(ShopCollection.name.asc())
        .all()
    )
    return render_template(
        "shop/collections.html",
        collections=active_collections,
    )


@shop_bp.route("/collections/<slug>")
def collection_detail(slug):
    collection = ShopCollection.query.filter_by(
        slug=slug,
        is_published=True,
    ).first_or_404()
    products = (
        ShopProduct.query.filter_by(
            collection_id=collection.id,
            is_published=True,
        )
        .order_by(ShopProduct.is_demo.asc(), ShopProduct.name.asc())
        .all()
    )
    return render_template(
        "shop/collection.html",
        collection=collection,
        products=products,
    )


@shop_bp.route("/")
def catalog():
    query = ShopProduct.query.filter_by(is_published=True)
    search = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "featured")

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                ShopProduct.name.ilike(pattern),
                ShopProduct.description.ilike(pattern),
                ShopProduct.category.ilike(pattern),
            )
        )
    if category in SHOP_CATEGORIES:
        query = query.filter_by(category=category)

    if sort == "price-low":
        query = query.order_by(ShopProduct.price_paise.asc().nulls_last())
    elif sort == "price-high":
        query = query.order_by(ShopProduct.price_paise.desc().nulls_last())
    elif sort == "newest":
        query = query.order_by(ShopProduct.created_at.desc())
    else:
        query = query.order_by(ShopProduct.is_demo.asc(), ShopProduct.name.asc())

    products = query.all()
    active_collections = (
        ShopCollection.query.filter_by(is_published=True)
        .order_by(ShopCollection.name.asc())
        .all()
    )
    return render_template(
        "shop/catalog.html",
        products=products,
        categories=SHOP_CATEGORIES,
        selected_category=category,
        search=search,
        selected_sort=sort,
        collections=active_collections,
    )


@shop_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = ShopProduct.query.filter_by(
        id=product_id,
        is_published=True,
    ).first_or_404()
    related = (
        ShopProduct.query.filter(
            ShopProduct.is_published.is_(True),
            ShopProduct.category == product.category,
            ShopProduct.id != product.id,
        )
        .order_by(ShopProduct.is_demo.asc(), ShopProduct.name.asc())
        .limit(4)
        .all()
    )
    reviews = (
        ShopReview.query.filter_by(product_id=product.id, status="approved")
        .order_by(ShopReview.created_at.desc())
        .all()
    )
    review_average = (
        db.session.query(func.avg(ShopReview.rating))
        .filter_by(product_id=product.id, status="approved")
        .scalar()
    )
    review_items = []
    if current_user.is_authenticated:
        eligible_items = (
            db.session.query(ShopOrderItem)
            .join(ShopOrder)
            .filter(
                ShopOrder.user_id == current_user.id,
                ShopOrder.status == "fulfilled",
                ShopOrderItem.product_id == product.id,
            )
            .all()
        )
        reviewed_item_ids = {
            item_id
            for (item_id,) in db.session.query(ShopReview.order_item_id)
            .filter(ShopReview.user_id == current_user.id)
            .all()
        }
        review_items = [
            item for item in eligible_items if item.id not in reviewed_item_ids
        ]
    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.description,
        "image": product.image_url,
        "offers": {
            "@type": "Offer",
            "priceCurrency": "INR",
            "price": f"{product.price_paise / 100:.2f}"
            if product.price_paise is not None
            else None,
            "availability": "https://schema.org/"
            + ("InStock" if product.stock_quantity > 0 else "OutOfStock"),
        },
    }
    if reviews and review_average is not None:
        product_schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": round(float(review_average), 1),
            "reviewCount": len(reviews),
        }
    return render_template(
        "shop/product.html",
        product=product,
        related_products=related,
        reviews=reviews,
        review_average=review_average,
        review_items=review_items,
        product_schema=product_schema,
    )


@shop_bp.route("/account")
@login_required
def account():
    orders = (
        ShopOrder.query.filter_by(user_id=current_user.id)
        .order_by(ShopOrder.created_at.desc())
        .all()
    )
    return render_template(
        "shop/account.html",
        orders=orders,
        statuses=ORDER_STATUSES,
    )


@shop_bp.route("/product/<int:product_id>/review", methods=["POST"])
@login_required
def submit_review(product_id):
    _require_csrf()
    product = ShopProduct.query.filter_by(
        id=product_id,
        is_published=True,
        is_demo=False,
    ).first_or_404()
    try:
        order_item_id = int(request.form.get("order_item_id", ""))
        rating = int(request.form.get("rating", ""))
    except ValueError:
        abort(400, description="Choose a valid completed purchase and rating.")
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    if not 1 <= rating <= 5 or not 3 <= len(title) <= 120:
        abort(400, description="Enter a review title and a rating from 1 to 5.")
    if not 10 <= len(body) <= 2000:
        abort(400, description="Review text must be between 10 and 2,000 characters.")
    eligible_item = (
        db.session.query(ShopOrderItem)
        .join(ShopOrder)
        .filter(
            ShopOrderItem.id == order_item_id,
            ShopOrderItem.product_id == product.id,
            ShopOrder.user_id == current_user.id,
            ShopOrder.status == "fulfilled",
        )
        .first()
    )
    if eligible_item is None:
        abort(403, description="Reviews are available only for fulfilled purchases.")
    if ShopReview.query.filter_by(order_item_id=eligible_item.id).first():
        flash("A review has already been submitted for this purchase.", "error")
        return redirect(url_for("shop.product_detail", product_id=product.id))
    db.session.add(
        ShopReview(
            product_id=product.id,
            user_id=current_user.id,
            order_item_id=eligible_item.id,
            rating=rating,
            title=title,
            body=body,
            status="pending",
        )
    )
    db.session.commit()
    flash("Thanks. Your review will appear after the store approves it.", "success")
    return redirect(url_for("shop.product_detail", product_id=product.id))


@shop_bp.route("/cart")
def cart():
    _remove_unavailable_items()
    rows, subtotal = _cart_products()
    return render_template("shop/cart.html", rows=rows, subtotal=subtotal)


@shop_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    _require_csrf()
    product = ShopProduct.query.filter_by(
        id=product_id,
        is_published=True,
    ).first_or_404()
    if product.is_demo or product.price_paise is None:
        flash("This is a sample listing, not available to purchase.", "error")
        return redirect(url_for("shop.product_detail", product_id=product.id))
    if product.stock_quantity < 1:
        flash("This item is currently out of stock.", "error")
        return redirect(url_for("shop.product_detail", product_id=product.id))

    cart = dict(_cart())
    key = str(product.id)
    quantity = int(cart.get(key, 0))
    if quantity >= product.stock_quantity:
        flash("You have added all available stock of this item.", "error")
    else:
        cart[key] = quantity + 1
        session["shop_cart"] = cart
        flash("Added to your bag.", "success")
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    _require_csrf()
    cart = dict(_cart())
    key = str(product_id)
    action = request.form.get("action")
    if action == "remove":
        cart.pop(key, None)
    else:
        try:
            quantity = int(request.form.get("quantity", ""))
        except ValueError:
            abort(400, description="Enter a valid quantity.")
        product = ShopProduct.query.filter_by(
            id=product_id,
            is_published=True,
            is_demo=False,
        ).first_or_404()
        if quantity < 1:
            cart.pop(key, None)
        elif quantity > product.stock_quantity:
            flash("The requested quantity is not available.", "error")
        else:
            cart[key] = quantity
    session["shop_cart"] = cart
    return redirect(url_for("shop.cart"))


@shop_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    _remove_unavailable_items()
    rows, subtotal = _cart_products()
    if not rows:
        flash("Your shopping bag is empty.", "error")
        return redirect(url_for("shop.catalog"))
    if any(
        row["product"].is_demo
        or row["product"].price_paise is None
        or row["product"].stock_quantity < row["quantity"]
        for row in rows
    ):
        session["shop_cart"] = {
            str(row["product"].id): row["quantity"]
            for row in rows
            if not row["product"].is_demo
            and row["product"].price_paise is not None
            and row["product"].stock_quantity >= row["quantity"]
        }
        flash("Your bag has an item that is no longer available. Please review it.", "error")
        return redirect(url_for("shop.cart"))

    if request.method == "GET":
        return _render_checkout(rows, subtotal)

    _require_csrf()
    if request.form.get("action") == "apply_coupon":
        code = request.form.get("coupon_code", "").strip().upper()
        coupon = ShopCoupon.query.filter_by(code=code, is_active=True).first()
        if coupon is None:
            flash("That coupon code is not valid or active.", "error")
        elif subtotal < coupon.minimum_subtotal_paise:
            flash("Your order does not meet the minimum for that coupon.", "error")
        else:
            session["shop_coupon_code"] = coupon.code
            flash("Coupon applied.", "success")
        return redirect(url_for("shop.checkout"))

    name = request.form.get("name", "").strip()
    phone = re.sub(r"[\s()-]", "", request.form.get("phone", ""))
    email = request.form.get("email", "").strip().lower() or current_user.email
    address = request.form.get("address", "").strip()
    postal_code = request.form.get("postal_code", "").strip()
    if not 2 <= len(name) <= 120:
        flash("Enter your name.", "error")
        return _render_checkout(rows, subtotal, 400, name, email)
    if not re.fullmatch(r"\+?[1-9]\d{7,14}", phone):
        flash("Enter a valid phone number, including country code if needed.", "error")
        return _render_checkout(rows, subtotal, 400, name, email)
    if email and (len(email) > 255 or not validate_email(email)):
        flash("Enter a valid email address or leave it blank.", "error")
        return _render_checkout(rows, subtotal, 400, name, email)
    if not 8 <= len(address) <= 1000:
        flash("Enter your complete delivery address.", "error")
        return _render_checkout(rows, subtotal, 400, name, email)
    if not re.fullmatch(r"\d{6}", postal_code):
        flash("Enter a valid 6-digit Indian PIN code.", "error")
        return _render_checkout(rows, subtotal, 400, name, email)

    coupon, discount = _active_cart_coupon(subtotal)

    order = ShopOrder(
        order_number=f"SLS-{secrets.token_hex(4).upper()}",
        customer_name=name,
        customer_phone=phone,
        customer_email=email or None,
        delivery_address=address,
        delivery_postal_code=postal_code,
        subtotal_paise=subtotal,
        discount_paise=discount,
        coupon_code=coupon.code if coupon else None,
        user_id=current_user.id,
    )
    for row in rows:
        product = row["product"]
        order.items.append(
            ShopOrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price_paise=product.price_paise,
                quantity=row["quantity"],
            )
        )
    db.session.add(order)
    db.session.commit()
    session.pop("shop_cart", None)
    session.pop("shop_coupon_code", None)

    message_lines = [
        f"Hello Sri Laxmi Silver, I'd like to confirm order {order.order_number}.",
        f"Name: {name}",
        f"Phone: {phone}",
        f"Address: {address}, PIN {postal_code}",
        "Items:",
    ]
    message_lines.extend(
        f"- {row['product'].name} x {row['quantity']} (₹{row['line_total'] / 100:.2f})"
        for row in rows
    )
    message_lines.extend(
        [
            f"Product subtotal: ₹{subtotal / 100:.2f}",
            *(
                [
                    f"Coupon {coupon.code}: -₹{discount / 100:.2f}",
                    f"Product total after discount: ₹{order.total_paise / 100:.2f}",
                ]
                if coupon
                else []
            ),
            "Delivery coverage (around 5 km) and charges are confirmed by the store before the order is final.",
            "Please confirm delivery coverage, charges and availability.",
        ]
    )
    whatsapp_url = (
        f"https://wa.me/{current_app.config['SHOP_WHATSAPP_NUMBER']}"
        f"?text={quote(chr(10).join(message_lines))}"
    )
    return render_template(
        "shop/order_confirmation.html",
        order=order,
        whatsapp_url=whatsapp_url,
    )


@shop_bp.route("/admin")
@_admin_required
def admin():
    products = ShopProduct.query.order_by(ShopProduct.created_at.desc()).all()
    order_status = request.args.get("status", "").strip()
    order_search = request.args.get("order_q", "").strip()[:100]
    order_query = ShopOrder.query
    if order_status in ORDER_STATUSES:
        order_query = order_query.filter_by(status=order_status)
    if order_search:
        pattern = f"%{order_search}%"
        order_query = order_query.filter(
            or_(
                ShopOrder.order_number.ilike(pattern),
                ShopOrder.customer_name.ilike(pattern),
                ShopOrder.customer_phone.ilike(pattern),
            )
        )
    orders = order_query.order_by(ShopOrder.created_at.desc()).limit(100).all()
    coupons = ShopCoupon.query.order_by(ShopCoupon.code.asc()).all()
    collections = ShopCollection.query.order_by(ShopCollection.name.asc()).all()
    reviews = (
        ShopReview.query.filter_by(status="pending")
        .order_by(ShopReview.created_at.asc())
        .all()
    )
    status_counts = dict(
        db.session.query(ShopOrder.status, func.count(ShopOrder.id))
        .group_by(ShopOrder.status)
        .all()
    )
    product_count = ShopProduct.query.count()
    live_product_count = ShopProduct.query.filter_by(
        is_published=True,
        is_demo=False,
    ).count()
    low_stock_count = ShopProduct.query.filter(
        ShopProduct.is_published.is_(True),
        ShopProduct.is_demo.is_(False),
        ShopProduct.stock_quantity.between(1, 5),
    ).count()
    out_of_stock_count = ShopProduct.query.filter_by(
        is_published=True,
        is_demo=False,
        stock_quantity=0,
    ).count()
    return render_template(
        "shop/admin.html",
        products=products,
        orders=orders,
        statuses=ORDER_STATUSES,
        coupons=coupons,
        reviews=reviews,
        collections=collections,
        status_counts=status_counts,
        product_count=product_count,
        live_product_count=live_product_count,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        pending_order_count=status_counts.get("awaiting_whatsapp", 0),
        order_status=order_status,
        order_search=order_search,
    )


@shop_bp.route("/admin/collections", methods=["POST"])
@_admin_required
def create_collection():
    _require_csrf()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if not 2 <= len(name) <= 100:
        flash("Collection names must be between 2 and 100 characters.", "error")
        return redirect(url_for("shop.admin", _anchor="collections"))
    if len(description) > 500:
        flash("Collection descriptions can be up to 500 characters.", "error")
        return redirect(url_for("shop.admin", _anchor="collections"))
    db.session.add(
        ShopCollection(
            name=name,
            slug=_new_collection_slug(name),
            description=description,
            is_published=request.form.get("is_published") == "on",
        )
    )
    db.session.commit()
    flash("Collection created.", "success")
    return redirect(url_for("shop.admin", _anchor="collections"))


@shop_bp.route("/admin/collections/<int:collection_id>/toggle", methods=["POST"])
@_admin_required
def toggle_collection(collection_id):
    _require_csrf()
    collection = db.session.get(ShopCollection, collection_id)
    if collection is None:
        abort(404)
    collection.is_published = not collection.is_published
    db.session.commit()
    flash("Collection visibility updated.", "success")
    return redirect(url_for("shop.admin", _anchor="collections"))


@shop_bp.route("/admin/coupons", methods=["POST"])
@_admin_required
def create_coupon():
    _require_csrf()
    code = request.form.get("code", "").strip().upper()
    discount_type = request.form.get("discount_type", "")
    raw_value = request.form.get("discount_value", "").strip()
    raw_minimum = request.form.get("minimum_subtotal", "").strip()
    if not re.fullmatch(r"[A-Z0-9_-]{3,40}", code):
        flash("Coupon codes must be 3–40 letters, numbers, hyphens or underscores.", "error")
        return redirect(url_for("shop.admin"))
    if ShopCoupon.query.filter_by(code=code).first():
        flash("That coupon code already exists.", "error")
        return redirect(url_for("shop.admin"))
    if discount_type == "percent":
        try:
            value = int(raw_value)
        except ValueError:
            value = 0
        if not 1 <= value <= 100:
            flash("Percentage discounts must be from 1 to 100.", "error")
            return redirect(url_for("shop.admin"))
    elif discount_type == "fixed":
        value = _parse_rupees(raw_value) or 0
        if value <= 0:
            flash("Enter a positive fixed discount in rupees.", "error")
            return redirect(url_for("shop.admin"))
    else:
        flash("Choose a valid coupon discount type.", "error")
        return redirect(url_for("shop.admin"))

    minimum = _parse_nonnegative_rupees(raw_minimum) if raw_minimum else 0
    if minimum is None:
        flash("Enter a valid minimum order amount or leave it blank.", "error")
        return redirect(url_for("shop.admin"))
    db.session.add(
        ShopCoupon(
            code=code,
            discount_type=discount_type,
            discount_value=value,
            minimum_subtotal_paise=minimum,
            is_active=True,
        )
    )
    db.session.commit()
    flash("Coupon created.", "success")
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/coupons/<int:coupon_id>/toggle", methods=["POST"])
@_admin_required
def toggle_coupon(coupon_id):
    _require_csrf()
    coupon = db.session.get(ShopCoupon, coupon_id)
    if coupon is None:
        abort(404)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    flash("Coupon status updated.", "success")
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/reviews/<int:review_id>", methods=["POST"])
@_admin_required
def moderate_review(review_id):
    _require_csrf()
    review = db.session.get(ShopReview, review_id)
    if review is None:
        abort(404)
    status = request.form.get("status", "")
    if status not in {"approved", "rejected"}:
        abort(400, description="Choose approve or reject.")
    review.status = status
    db.session.commit()
    flash("Review moderation updated.", "success")
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/products", methods=["POST"])
@_admin_required
def create_product():
    _require_csrf()
    values, error = _product_form_values()
    if error:
        flash(error, "error")
        return redirect(url_for("shop.admin"))
    product = ShopProduct(slug=_new_slug(values["name"]), **values)
    db.session.add(product)
    db.session.commit()
    flash("Product added to the shop.", "success")
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/products/<int:product_id>", methods=["POST"])
@_admin_required
def update_product(product_id):
    _require_csrf()
    product = db.session.get(ShopProduct, product_id)
    if product is None:
        abort(404)
    values, error = _product_form_values()
    if error:
        flash(error, "error")
        return redirect(url_for("shop.admin"))
    if product.name != values["name"]:
        product.slug = _new_slug(values["name"], exclude_id=product.id)
    product.name = values["name"]
    product.category = values["category"]
    product.collection_id = values["collection_id"]
    product.description = values["description"]
    product.image_url = values["image_url"]
    product.price_paise = values["price_paise"]
    product.stock_quantity = values["stock_quantity"]
    product.is_demo = values["is_demo"]
    product.is_published = values["is_published"]
    db.session.commit()
    flash("Product updated.", "success")
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/orders/<int:order_id>", methods=["POST"])
@_admin_required
def update_order(order_id):
    _require_csrf()
    order = db.session.get(ShopOrder, order_id)
    if order is None:
        abort(404)
    next_status = request.form.get("status", "")
    if next_status not in ORDER_STATUSES:
        abort(400, description="Choose a valid order status.")

    if next_status not in ORDER_TRANSITIONS[order.status]:
        flash("That order status change is not allowed.", "error")
        return redirect(url_for("shop.admin"))

    if next_status == "confirmed" and not order.stock_reserved:
        for item in order.items:
            product = db.session.get(ShopProduct, item.product_id)
            if product and product.stock_quantity < item.quantity:
                flash(
                    f"Not enough stock to confirm {item.product_name}.",
                    "error",
                )
                return redirect(url_for("shop.admin"))
        for item in order.items:
            product = db.session.get(ShopProduct, item.product_id)
            if product:
                product.stock_quantity -= item.quantity
        order.stock_reserved = True
    elif next_status == "cancelled" and order.stock_reserved:
        for item in order.items:
            product = db.session.get(ShopProduct, item.product_id)
            if product:
                product.stock_quantity += item.quantity
        order.stock_reserved = False

    order.status = next_status
    db.session.commit()
    flash("Order status updated.", "success")
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/seed-demo", methods=["POST"])
@_admin_required
def seed_demo_products():
    _require_csrf()
    added = seed_demo_catalog()
    flash(
        "Sample products added. They are visible as examples but cannot be ordered."
        if added
        else "Sample listings have already been added.",
        "success",
    )
    return redirect(url_for("shop.admin"))


@shop_bp.route("/admin/analytics")
@_admin_required
def analytics():
    orders_by_status = (
        db.session.query(ShopOrder.status, func.count(ShopOrder.id))
        .group_by(ShopOrder.status)
        .all()
    )
    product_count = ShopProduct.query.count()
    live_product_count = ShopProduct.query.filter_by(
        is_published=True,
        is_demo=False,
    ).count()
    return render_template(
        "shop/analytics.html",
        orders_by_status=orders_by_status,
        product_count=product_count,
        live_product_count=live_product_count,
        statuses=ORDER_STATUSES,
    )
