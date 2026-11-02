from ..extensions import db
from ..models import Page, PageVersion, Section


def save_generated_website(website, plan, content):
    existing_pages = Page.query.filter_by(
        website_id=website.id
    ).all()

    for page in existing_pages:
        db.session.delete(page)

    db.session.flush()

    generated_pages = []

    for page_plan in plan["pages"]:
        slug = page_plan["slug"]
        title = page_plan["title"]

        page = Page(
            website_id=website.id,
            title=title,
            slug=slug,
            status="draft",
            is_homepage=(slug == "home"),
        )

        db.session.add(page)
        db.session.flush()

        page_content = content.get(slug, {})
        section_types = page_plan.get("sections", [])

        for position, section_type in enumerate(section_types):
            section_content = _get_section_content(
                slug,
                section_type,
                page_content,
            )

            section = Section(
                page_id=page.id,
                section_type=section_type,
                position=position,
                content=section_content,
                styles={
                    "style": plan["website"].get(
                        "style",
                        "modern",
                    )
                },
            )

            db.session.add(section)

        snapshot = {
            "page": {
                "title": title,
                "slug": slug,
                "status": "draft",
                "is_homepage": slug == "home",
            },
            "sections": [
                {
                    "type": section_type,
                    "content": _get_section_content(
                        slug,
                        section_type,
                        page_content,
                    ),
                }
                for section_type in section_types
            ],
        }

        version = PageVersion(
            page_id=page.id,
            version_number=1,
            snapshot=snapshot,
        )

        db.session.add(version)
        generated_pages.append(page)

    db.session.commit()

    return generated_pages


def _get_section_content(
    slug,
    section_type,
    page_content,
):
    if slug == "home":
        mapping = {
            "hero": page_content.get("hero", {}),
            "about": page_content.get("about", {}),
            "services": page_content.get("services", {}),
            "why-choose-us": page_content.get(
                "why_choose_us",
                {},
            ),
            "call-to-action": page_content.get(
                "cta",
                {},
            ),
        }

        return mapping.get(section_type, {})

    if slug == "about":
        mapping = {
            "introduction": page_content.get(
                "introduction",
                {},
            ),
            "values": {
                "items": page_content.get(
                    "values",
                    [],
                )
            },
            "call-to-action": page_content.get(
                "cta",
                {},
            ),
        }

        return mapping.get(section_type, {})

    if slug == "services":
        mapping = {
            "services-introduction": page_content.get(
                "hero",
                {},
            ),
            "service-list": {
                "items": page_content.get(
                    "items",
                    [],
                )
            },
            "call-to-action": page_content.get(
                "cta",
                {},
            ),
        }

        return mapping.get(section_type, {})

    if slug == "contact":
        mapping = {
            "contact-introduction": page_content.get(
                "hero",
                {},
            ),
            "contact-form": page_content.get(
                "form",
                {},
            ),
            "call-to-action": page_content.get(
                "cta",
                {},
            ),
        }

        return mapping.get(section_type, {})

    return {}