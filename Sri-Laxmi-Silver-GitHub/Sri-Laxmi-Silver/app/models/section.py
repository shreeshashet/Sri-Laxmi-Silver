from datetime import datetime, timezone

from ..extensions import db


class Section(db.Model):
    __tablename__ = "sections"

    id = db.Column(db.Integer, primary_key=True)

    page_id = db.Column(
        db.Integer,
        db.ForeignKey("pages.id"),
        nullable=False,
        index=True,
    )

    section_type = db.Column(
        db.String(100),
        nullable=False,
    )

    position = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    content = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
    )

    styles = db.Column(
        db.JSON,
        nullable=False,
        default=dict,
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
            "sections",
            lazy=True,
            cascade="all, delete-orphan",
            order_by="Section.position",
        ),
    )