from ..models import Website


def generate_page_content(website: Website) -> dict:
    """
    Generate initial website copy from the saved website brief.

    This is a deterministic content layer.
    Later, an AI provider can replace the copy-generation logic.
    """

    brief = website.brief

    if brief is None:
        raise ValueError("Website brief not found.")

    business_name = website.name
    business_type = brief.business_type
    description = brief.description
    audience = brief.audience or "our clients"
    goals = brief.goals or "deliver a professional experience"
    style = brief.style or "modern"

    return {
        "home": {
            "seo_title": f"{business_name} | {business_type}",
            "seo_description": (
                f"{business_name} provides {business_type.lower()} "
                f"services for {audience.lower()}."
            ),

            "hero": {
                "eyebrow": business_type,
                "headline": (
                    f"Reliable {business_type} solutions "
                    f"for every event."
                ),
                "description": description,
                "primary_cta": "Get Started",
                "secondary_cta": "Explore Services",
            },

            "about": {
                "title": f"About {business_name}",
                "text": (
                    f"{business_name} is focused on delivering "
                    f"professional {business_type.lower()} services. "
                    f"Our approach is built around reliability, "
                    f"quality, and a smooth experience from planning "
                    f"to completion."
                ),
            },

            "services": {
                "title": "Our Services",
                "intro": (
                    f"We provide dependable {business_type.lower()} "
                    f"solutions designed around the needs of "
                    f"{audience.lower()}."
                ),
                "items": [
                    {
                        "title": "Event Staffing",
                        "description": (
                            "Professional staff prepared to support "
                            "events of different sizes and requirements."
                        ),
                    },
                    {
                        "title": "On-Site Support",
                        "description": (
                            "Reliable on-site personnel helping your "
                            "event run smoothly from start to finish."
                        ),
                    },
                    {
                        "title": "Flexible Staffing",
                        "description": (
                            "Staffing solutions that can adapt to your "
                            "schedule, venue, and event requirements."
                        ),
                    },
                ],
            },

            "why_choose_us": {
                "title": "Why Choose Us",
                "items": [
                    {
                        "title": "Reliable",
                        "description": (
                            "Dependable people and professional service "
                            "when your event needs it most."
                        ),
                    },
                    {
                        "title": "Professional",
                        "description": (
                            "A service-focused team that understands "
                            "the importance of presentation and trust."
                        ),
                    },
                    {
                        "title": "Flexible",
                        "description": (
                            "Solutions designed around your event rather "
                            "than forcing your event into a fixed model."
                        ),
                    },
                ],
            },

            "cta": {
                "title": "Let's make your next event run smoothly.",
                "text": (
                    f"Tell us what you need and discover how "
                    f"{business_name} can support your event."
                ),
                "button": "Get Started",
            },
        },

        "about": {
            "seo_title": f"About {business_name}",
            "seo_description": (
                f"Learn more about {business_name} and our "
                f"{business_type.lower()} services."
            ),

            "hero": {
                "title": f"About {business_name}",
                "description": description,
            },

            "introduction": {
                "title": "Built Around Reliability",
                "text": (
                    f"Our goal is simple: {goals.lower()}. "
                    f"We combine professional service with a "
                    f"practical understanding of what successful "
                    f"events require."
                ),
            },

            "values": [
                {
                    "title": "Trust",
                    "description": (
                        "Clear communication and dependable service."
                    ),
                },
                {
                    "title": "Quality",
                    "description": (
                        "Professional standards at every stage."
                    ),
                },
                {
                    "title": "Commitment",
                    "description": (
                        "Focused on helping every event succeed."
                    ),
                },
            ],

            "cta": {
                "title": "Need reliable event support?",
                "button": "Contact Us",
            },
        },

        "services": {
            "seo_title": f"Services | {business_name}",
            "seo_description": (
                f"Explore {business_name}'s {business_type.lower()} "
                f"services."
            ),

            "hero": {
                "title": "Services Designed Around Your Event",
                "description": (
                    f"Our {business_type.lower()} services are designed "
                    f"to give {audience.lower()} reliable support."
                ),
            },

            "items": [
                {
                    "title": "Event Staffing",
                    "description": (
                        "Professional personnel for event-day "
                        "operations and support."
                    ),
                },
                {
                    "title": "Hospitality Support",
                    "description": (
                        "Friendly and professional staff helping "
                        "create a smooth guest experience."
                    ),
                },
                {
                    "title": "Event Operations",
                    "description": (
                        "Practical staffing support for the operational "
                        "needs of your event."
                    ),
                },
            ],

            "cta": {
                "title": "Have an event coming up?",
                "text": (
                    "Let's discuss your staffing requirements."
                ),
                "button": "Get Started",
            },
        },

        "contact": {
            "seo_title": f"Contact {business_name}",
            "seo_description": (
                f"Contact {business_name} about your "
                f"{business_type.lower()} requirements."
            ),

            "hero": {
                "title": "Let's Talk About Your Event",
                "description": (
                    "Tell us about your event and what kind of "
                    "support you need."
                ),
            },

            "form": {
                "name_label": "Your Name",
                "email_label": "Email Address",
                "phone_label": "Phone Number",
                "message_label": "Tell us about your event",
                "button": "Send Enquiry",
            },

            "cta": {
                "title": "Ready to get started?",
                "text": (
                    f"Contact {business_name} today and let's plan "
                    f"the right support for your event."
                ),
            },
        },

        "meta": {
            "business_name": business_name,
            "business_type": business_type,
            "audience": audience,
            "goals": goals,
            "style": style,
        },
    }