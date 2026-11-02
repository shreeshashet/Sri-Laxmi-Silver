from datetime import datetime, timezone

from ..extensions import db


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)

    website_id = db.Column(
        db.Integer,
        db.ForeignKey("websites.id"),
        nullable=False,
        index=True,
    )

    filename = db.Column(
        db.String(255),
        nullable=False,
    )

    url = db.Column(
        db.String(1000),
        nullable=False,
    )

    asset_type = db.Column(
        db.String(50),
        nullable=False,
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    website = db.relationship(
        "Website",
        backref=db.backref(
            "assets",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )