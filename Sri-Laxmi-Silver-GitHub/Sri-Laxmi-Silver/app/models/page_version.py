from datetime import datetime, timezone

from ..extensions import db


class PageVersion(db.Model):
    __tablename__ = "page_versions"

    id = db.Column(db.Integer, primary_key=True)

    page_id = db.Column(
        db.Integer,
        db.ForeignKey("pages.id"),
        nullable=False,
        index=True,
    )

    version_number = db.Column(
        db.Integer,
        nullable=False,
    )

    snapshot = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    page = db.relationship(
        "Page",
        backref=db.backref(
            "versions",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )