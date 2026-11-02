from ..models import Website


def generate_website_plan(website: Website) -> dict:
    """
    Build a structured website plan from the saved website brief.

    This is the first generation layer.
    Later, the AI provider will replace the rule-based content here.
    """

    brief = website.brief

    if brief is None:
        raise ValueError("Website brief not found.")

    business_name = website.name
    business_type = brief.business_type
    description = brief.description
    audience = brief.audience or ""
    goals = brief.goals or ""
    style = brief.style or "modern"

    return {
        "website": {
            "name": business_name,
            "business_type": business_type,
            "style": style,
        },

        "brief": {
            "description": description,
            "audience": audience,
            "goals": goals,
        },

        "pages": [
            {
                "slug": "home",
                "title": "Home",
                "sections": [
                    "hero",
                    "about",
                    "services",
                    "why-choose-us",
                    "call-to-action",
                ],
            },
            {
                "slug": "about",
                "title": "About",
                "sections": [
                    "introduction",
                    "values",
                    "call-to-action",
                ],
            },
            {
                "slug": "services",
                "title": "Services",
                "sections": [
                    "services-introduction",
                    "service-list",
                    "call-to-action",
                ],
            },
            {
                "slug": "contact",
                "title": "Contact",
                "sections": [
                    "contact-introduction",
                    "contact-form",
                    "call-to-action",
                ],
            },
        ],
    }