import re

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    ShopCoupon,
    ShopCollection,
    ShopOrder,
    ShopOrderItem,
    ShopProduct,
    ShopReview,
    User,
)


@pytest.fixture
def shop_app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SHOP_ADMIN_EMAILS": {"owner@example.com"},
        }
    )
    with app.app_context():
        db.create_all()
        demo = ShopProduct(
            name="Demo earrings",
            slug="demo-earrings",
            category="Jewellery",
            description="Illustrative example only.",
            image_url="/static/images/sljw-emblem.png",
            price_paise=None,
            stock_quantity=0,
            is_published=True,
            is_demo=True,
        )
        product = ShopProduct(
            name="Silver bracelet",
            slug="silver-bracelet",
            category="Jewellery",
            description="An actual catalog test product.",
            image_url="/static/images/sljw-emblem.png",
            price_paise=249900,
            stock_quantity=3,
            is_published=True,
            is_demo=False,
        )
        owner = User(email="owner@example.com", name="Shop owner")
        owner.set_password("secure-test-password")
        db.session.add_all([demo, product, owner])
        db.session.commit()
        product_id = product.id
        demo_id = demo.id
    yield app, product_id, demo_id
    with app.app_context():
        db.session.remove()
        db.drop_all()


def _csrf_token(client, path):
    response = client.get(path)
    assert response.status_code == 200
    token = re.search(
        rb'name="csrf_token" value="([^"]+)"',
        response.data,
    )
    if token:
        return token.group(1).decode()
    with client.session_transaction() as browser_session:
        return browser_session["_shop_csrf_token"]


def _login_owner(client):
    return client.post(
        "/auth/login",
        data={
            "email": "owner@example.com",
            "password": "secure-test-password",
        },
    )


def test_catalog_search_and_demo_items_are_not_orderable(shop_app):
    app, product_id, demo_id = shop_app
    client = app.test_client()

    response = client.get("/shop/?q=bracelet")
    assert response.status_code == 200
    assert b"Silver bracelet" in response.data
    assert b"Demo earrings" not in response.data

    token = _csrf_token(client, f"/shop/product/{product_id}")
    response = client.post(
        f"/shop/cart/add/{demo_id}",
        data={"csrf_token": token},
    )
    assert response.status_code == 302
    assert client.get("/shop/cart").status_code == 200
    with client.session_transaction() as browser_session:
        assert browser_session.get("shop_cart", {}) == {}


def test_information_pages_are_available_and_explain_ordering(shop_app):
    app, _, _ = shop_app
    client = app.test_client()

    about_response = client.get("/shop/about")
    contact_response = client.get("/shop/contact")
    help_response = client.get("/shop/help")
    privacy_response = client.get("/shop/privacy")
    assert about_response.status_code == 200
    assert b"Silver is more than a moment." in about_response.data
    assert contact_response.status_code == 200
    assert b"No. 14, Kalyan Nagar" in contact_response.data
    assert b"Store hours are not listed here" in contact_response.data
    assert help_response.status_code == 200
    assert b"Ordering help" in help_response.data
    assert privacy_response.status_code == 200
    assert b"your account email" in privacy_response.data

    assert b"not confirmed until the store replies" in help_response.data
    assert b"Online payment is not available" in help_response.data
    assert b"returns and exchanges policy has not been published" in help_response.data


def test_music_player_is_available_on_home_and_shop_pages(shop_app):
    app, _, _ = shop_app
    client = app.test_client()

    home_response = client.get("/")
    catalog_response = client.get("/shop/")
    assert home_response.status_code == 200
    assert catalog_response.status_code == 200
    assert b'class="music-toggle"' in home_response.data
    assert b'class="music-toggle"' in catalog_response.data
    assert b'aria-pressed="false"' in home_response.data
    assert b"Music off" in catalog_response.data


def test_guest_checkout_requires_customer_account(shop_app):
    app, product_id, _ = shop_app
    client = app.test_client()
    token = _csrf_token(client, f"/shop/product/{product_id}")
    client.post(f"/shop/cart/add/{product_id}", data={"csrf_token": token})

    response = client.get("/shop/checkout")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert "next=%2Fshop%2Fcheckout" in response.headers["Location"]


def test_customer_can_prepare_whatsapp_order_with_delivery_estimate(shop_app):
    app, product_id, _ = shop_app
    client = app.test_client()
    token = _csrf_token(client, f"/shop/product/{product_id}")

    response = client.post(
        f"/shop/cart/add/{product_id}",
        data={"csrf_token": token},
    )
    assert response.status_code == 302
    assert client.get("/shop/cart").status_code == 200
    _login_owner(client)

    response = client.post(
        "/shop/checkout",
        data={
            "csrf_token": token,
            "name": "Asha Rao",
            "phone": "+919876543210",
            "email": "asha@example.com",
            "address": "14 Market Road, Nagarabhavi",
            "postal_code": "560072",
        },
    )
    assert response.status_code == 200
    assert b"wa.me" in response.data
    assert b"Within 7 days" in response.data
    assert b"not confirmed" in response.data
    assert b"Sri Laxmi Silver" in response.data
    account_response = client.get("/shop/account")
    assert account_response.status_code == 200
    assert b"My orders." in account_response.data

    with app.app_context():
        order = db.session.query(ShopOrder).one()
        assert order.customer_name == "Asha Rao"
        assert order.subtotal_paise == 249900
        assert order.status == "awaiting_whatsapp"
        assert order.user_id is not None
        assert order.customer_email == "asha@example.com"


def test_admin_is_restricted_and_can_add_catalog_product(shop_app):
    app, _, _ = shop_app
    client = app.test_client()

    admin_redirect = client.get("/shop/admin")
    assert admin_redirect.status_code == 302
    assert "/auth/login" in admin_redirect.headers["Location"]
    _login_owner(client)
    assert client.get("/shop/admin").status_code == 200
    client.get("/auth/logout")
    assert client.get("/shop/admin").status_code == 302
    _login_owner(client)
    token = _csrf_token(client, "/shop/admin")
    response = client.post(
        "/shop/admin/products",
        data={
            "csrf_token": token,
            "name": "Silver ring",
            "category": "Jewellery",
            "price": "1250.50",
            "stock_quantity": "4",
            "image_url": "/static/images/sljw-emblem.png",
            "description": "A confirmed product listing.",
            "is_published": "on",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        product = ShopProduct.query.filter_by(name="Silver ring").one()
        assert product.price_paise == 125050
        assert product.is_published is True
        assert product.is_demo is False


def test_admin_can_create_and_publish_named_collections(shop_app):
    app, product_id, _ = shop_app
    client = app.test_client()
    _login_owner(client)
    token = _csrf_token(client, "/shop/admin")

    response = client.post(
        "/shop/admin/collections",
        data={
            "csrf_token": token,
            "name": "Festival Gifts",
            "description": "Silver pieces chosen for celebrations.",
            "is_published": "on",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        collection = ShopCollection.query.filter_by(name="Festival Gifts").one()
        collection_id = collection.id
        product = db.session.get(ShopProduct, product_id)
        product.collection_id = collection_id
        db.session.commit()

    response = client.get("/shop/collections")
    assert response.status_code == 200
    assert b"Festival Gifts" in response.data
    response = client.get("/shop/collections/festival-gifts")
    assert response.status_code == 200
    assert b"Silver bracelet" in response.data

    token = _csrf_token(client, "/shop/admin")
    response = client.post(
        f"/shop/admin/collections/{collection_id}/toggle",
        data={"csrf_token": token},
    )
    assert response.status_code == 302
    assert client.get("/shop/collections/festival-gifts").status_code == 404


def test_checkout_rejects_missing_csrf_and_invalid_pin(shop_app):
    app, product_id, _ = shop_app
    client = app.test_client()
    token = _csrf_token(client, f"/shop/product/{product_id}")
    client.post(f"/shop/cart/add/{product_id}", data={"csrf_token": token})
    _login_owner(client)

    missing_csrf = client.post(
        "/shop/checkout",
        data={"name": "Asha Rao"},
    )
    assert missing_csrf.status_code == 400

    invalid_pin = client.post(
        "/shop/checkout",
        data={
            "csrf_token": token,
            "name": "Asha Rao",
            "phone": "9876543210",
            "address": "Market Road, Nagarabhavi",
            "postal_code": "56007",
        },
    )
    assert invalid_pin.status_code == 400


def test_order_stock_is_reserved_released_and_transitions_are_limited(shop_app):
    app, product_id, _ = shop_app
    client = app.test_client()
    token = _csrf_token(client, f"/shop/product/{product_id}")
    client.post(f"/shop/cart/add/{product_id}", data={"csrf_token": token})
    _login_owner(client)
    response = client.post(
        "/shop/checkout",
        data={
            "csrf_token": token,
            "name": "Asha Rao",
            "phone": "9876543210",
            "address": "14 Market Road, Nagarabhavi",
            "postal_code": "560072",
        },
    )
    assert response.status_code == 200
    with app.app_context():
        order_id = db.session.query(ShopOrder).one().id

    token = _csrf_token(client, "/shop/admin")
    response = client.post(
        f"/shop/admin/orders/{order_id}",
        data={"csrf_token": token, "status": "confirmed"},
    )
    assert response.status_code == 302
    with app.app_context():
        product = db.session.get(ShopProduct, product_id)
        order = db.session.get(ShopOrder, order_id)
        assert product.stock_quantity == 2
        assert order.stock_reserved is True

    response = client.post(
        f"/shop/admin/orders/{order_id}",
        data={"csrf_token": token, "status": "cancelled"},
    )
    assert response.status_code == 302
    with app.app_context():
        product = db.session.get(ShopProduct, product_id)
        order = db.session.get(ShopOrder, order_id)
        assert product.stock_quantity == 3
        assert order.stock_reserved is False

    response = client.post(
        f"/shop/admin/orders/{order_id}",
        data={"csrf_token": token, "status": "fulfilled"},
    )
    assert response.status_code == 302
    with app.app_context():
        order = db.session.get(ShopOrder, order_id)
        assert order.status == "cancelled"


def test_coupon_is_admin_created_and_applied_to_customer_order(shop_app):
    app, product_id, _ = shop_app
    client = app.test_client()
    _login_owner(client)
    token = _csrf_token(client, "/shop/admin")
    response = client.post(
        "/shop/admin/coupons",
        data={
            "csrf_token": token,
            "code": "SAVE100",
            "discount_type": "fixed",
            "discount_value": "100",
            "minimum_subtotal": "0",
        },
    )
    assert response.status_code == 302

    token = _csrf_token(client, f"/shop/product/{product_id}")
    client.post(f"/shop/cart/add/{product_id}", data={"csrf_token": token})
    response = client.post(
        "/shop/checkout",
        data={
            "csrf_token": token,
            "action": "apply_coupon",
            "coupon_code": "save100",
        },
    )
    assert response.status_code == 302
    response = client.post(
        "/shop/checkout",
        data={
            "csrf_token": token,
            "name": "Shop owner",
            "phone": "9876543210",
            "address": "14 Market Road, Nagarabhavi",
            "postal_code": "560072",
        },
    )
    assert response.status_code == 200
    assert b"Products after discount" in response.data
    with app.app_context():
        order = db.session.query(ShopOrder).one()
        coupon = db.session.query(ShopCoupon).one()
        assert coupon.code == "SAVE100"
        assert order.discount_paise == 10000
        assert order.total_paise == 239900
        assert order.coupon_code == coupon.code


def test_only_fulfilled_buyers_can_submit_reviews_and_admin_moderates(shop_app):
    app, product_id, _ = shop_app
    with app.app_context():
        owner = User.query.filter_by(email="owner@example.com").one()
        order = ShopOrder(
            order_number="SLJW-REVIEW1",
            customer_name="Shop owner",
            customer_phone="9876543210",
            delivery_address="14 Market Road, Nagarabhavi",
            delivery_postal_code="560072",
            subtotal_paise=249900,
            user_id=owner.id,
            status="fulfilled",
        )
        order.items.append(
            ShopOrderItem(
                product_id=product_id,
                product_name="Silver bracelet",
                unit_price_paise=249900,
                quantity=1,
            )
        )
        db.session.add(order)
        db.session.commit()
        order_item_id = order.items[0].id

    client = app.test_client()
    _login_owner(client)
    token = _csrf_token(client, f"/shop/product/{product_id}")
    response = client.post(
        f"/shop/product/{product_id}/review",
        data={
            "csrf_token": token,
            "order_item_id": order_item_id,
            "rating": "5",
            "title": "Lovely finish",
            "body": "The piece is beautiful and the finish is excellent.",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        review = ShopReview.query.one()
        assert review.status == "pending"
        review_id = review.id

    token = _csrf_token(client, "/shop/admin")
    response = client.post(
        f"/shop/admin/reviews/{review_id}",
        data={"csrf_token": token, "status": "approved"},
    )
    assert response.status_code == 302
    assert b"Lovely finish" in client.get(f"/shop/product/{product_id}").data


def test_location_and_free_search_engine_routes(shop_app):
    app, _, _ = shop_app
    client = app.test_client()
    contact = client.get("/shop/contact")
    assert b"store-map" in contact.data
    assert b"instagram.com/sri_laxmi_silver_" in contact.data
    assert b"Sri Laxmi Silver" in client.get("/").data
    assert b"<urlset" in client.get("/sitemap.xml").data
    assert b"Sitemap:" in client.get("/robots.txt").data
