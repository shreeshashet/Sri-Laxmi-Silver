from flask import Flask, Response, render_template, url_for
from xml.sax.saxutils import escape

from .config import Config
from .extensions import db, migrate, login_manager


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    # Import models so SQLAlchemy knows about them.
    from .models import (
        Asset,
        Page,
        PageVersion,
        Project,
        Section,
        SEO,
        ShopCollection,
        ShopOrder,
        ShopOrderItem,
        ShopProduct,
        User,
        Website,
        WebsiteBrief,
    )

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Authentication
    from .auth import auth_bp

    app.register_blueprint(auth_bp)

    # Dashboard
    from .dashboard import dashboard_bp

    app.register_blueprint(dashboard_bp)

    # Website builder
    from .builder import builder_bp

    app.register_blueprint(builder_bp)

    from .shop import shop_bp

    app.register_blueprint(shop_bp)

    @app.cli.command("seed-shop-demo")
    def seed_shop_demo():
        """Load clearly labelled, non-purchasable sample products."""
        from .shop.routes import seed_demo_catalog

        created_count = seed_demo_catalog()
        if created_count:
            print(f"Added {created_count} non-purchasable sample products.")
        else:
            print("Sample products are already present.")

    @app.template_filter("inr")
    def format_inr(amount_paise):
        return f"₹{amount_paise / 100:,.2f}"

    @app.route("/robots.txt")
    def robots_txt():
        return Response(
            f"User-agent: *\nAllow: /\nSitemap: {url_for('sitemap', _external=True)}\n",
            mimetype="text/plain",
        )

    @app.route("/sitemap.xml")
    def sitemap():
        page_urls = [
            url_for("home", _external=True),
            url_for("shop.catalog", _external=True),
            url_for("shop.collections", _external=True),
            url_for("shop.about", _external=True),
            url_for("shop.contact", _external=True),
            url_for("shop.help_page", _external=True),
            url_for("shop.privacy", _external=True),
        ]
        page_urls.extend(
            url_for("shop.collection_detail", slug=collection.slug, _external=True)
            for collection in ShopCollection.query.filter_by(is_published=True).all()
        )
        page_urls.extend(
            url_for("shop.product_detail", product_id=product.id, _external=True)
            for product in ShopProduct.query.filter_by(
                is_published=True,
                is_demo=False,
            ).all()
        )
        entries = "".join(
            f"<url><loc>{escape(page_url)}</loc></url>"
            for page_url in page_urls
        )
        return Response(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{entries}</urlset>",
            mimetype="application/xml",
        )

    # Sri Laxmi Silver storefront landing page
    @app.route("/")
    def home():
        featured_products = (
            ShopProduct.query.filter_by(is_published=True)
            .order_by(ShopProduct.is_demo.asc(), ShopProduct.name.asc())
            .limit(4)
            .all()
        )
        return render_template(
            "home.html",
            featured_products=featured_products,
        )

    return app
