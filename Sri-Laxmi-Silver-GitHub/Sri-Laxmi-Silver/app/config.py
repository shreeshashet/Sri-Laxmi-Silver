import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-only-change-this-secret",
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///sljw.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    SHOP_ADMIN_EMAILS = {
        email.strip().lower()
        for email in os.getenv("SHOP_ADMIN_EMAILS", "").split(",")
        if email.strip()
    }

    SHOP_WHATSAPP_NUMBER = os.getenv(
        "SHOP_WHATSAPP_NUMBER",
        "917259770322",
    )