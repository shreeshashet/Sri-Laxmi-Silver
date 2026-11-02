from datetime import datetime, timezone

from ..extensions import db


class Page(db.Model):
    __tablename__ = "pages"

    id = db.Column(db.Integer, primary_key=True)

    website_id = db.Column(
        db.Integer,
        db.ForeignKey("websites.id"),
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(200), nullable=False)

    slug = db.Column(db.String(200), nullable=False)

    status = db.Column(
        db.String(50),
        nullable=False,
        default="draft",
    )

    is_homepage = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
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

    website = db.relationship(
        "Website",
        backref=db.backref(
            "pages",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )