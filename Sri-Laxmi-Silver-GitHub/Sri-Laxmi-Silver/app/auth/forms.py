import re


def validate_email(email):
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def validate_password(password):
    return (
        isinstance(password, str)
        and len(password) >= 8
    )