from datetime import datetime, timezone

from ..extensions import db


class WebsiteBrief(db.Model):
    __tablename__ = "website_briefs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    website_id = db.Column(
        db.Integer,
        db.ForeignKey("websites.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    business_type = db.Column(
        db.String(200),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    audience = db.Column(
        db.Text,
        nullable=True,
    )

    goals = db.Column(
        db.Text,
        nullable=True,
    )

    style = db.Column(
        db.String(100),
        nullable=False,
        default="modern",
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
            "brief",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )