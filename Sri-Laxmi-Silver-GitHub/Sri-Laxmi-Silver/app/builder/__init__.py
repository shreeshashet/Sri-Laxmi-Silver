from flask import Blueprint


builder_bp = Blueprint(
    "builder",
    __name__,
    url_prefix="/builder",
)