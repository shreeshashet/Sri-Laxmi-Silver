from datetime import datetime, timezone

from ..extensions import db


class SEO(db.Model):
    __tablename__ = "seo_settings"

    id = db.Column(db.Integer, primary_key=True)

    page_id = db.Column(
        db.Integer,
        db.ForeignKey("pages.id"),
        nullable=False,
        unique=True,
    )

    title = db.Column(
        db.String(255),
        nullable=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    keywords = db.Column(
        db.Text,
        nullable=True,
    )

    canonical_url = db.Column(
        db.String(1000),
        nullable=True,
    )

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

    page = db.relationship(
        "Page",
        backref=db.backref(
            "seo",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )