from datetime import datetime, timezone

from ..extensions import db


class Website(db.Model):
    __tablename__ = "websites"

    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(200), nullable=False)

    subdomain = db.Column(
        db.String(100),
        unique=True,
        nullable=True,
        index=True,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="draft",
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

    project = db.relationship(
        "Project",
        backref=db.backref(
            "websites",
            lazy=True,
            cascade="all, delete-orphan",
        ),
    )