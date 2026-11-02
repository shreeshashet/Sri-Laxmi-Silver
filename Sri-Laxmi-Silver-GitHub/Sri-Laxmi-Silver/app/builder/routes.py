from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user

from . import builder_bp
from ..extensions import db
from ..models import (
    Page,
    Project,
    Website,
    WebsiteBrief,
    Section,
    PageVersion,
)
from ..generator.service import generate_website_plan
from ..generator.content import generate_page_content
from ..generator.persistence import save_generated_website


@builder_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_website():

    if request.method == "GET":
        return render_template(
            "builder/new.html"
        )

    business_name = request.form.get(
        "business_name",
        "",
    ).strip()

    business_type = request.form.get(
        "business_type",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    audience = request.form.get(
        "audience",
        "",
    ).strip()

    goals = request.form.get(
        "goals",
        "",
    ).strip()

    style = request.form.get(
        "style",
        "modern",
    ).strip()

    if not business_name:
        return "Business name is required", 400

    if not business_type:
        return "Business type is required", 400

    if not description:
        return "Business description is required", 400

    project = Project(
        user_id=current_user.id,
        name=business_name,
        description=description,
    )

    db.session.add(project)
    db.session.flush()

    website = Website(
        project_id=project.id,
        name=business_name,
        status="draft",
    )

    db.session.add(website)
    db.session.flush()

    brief = WebsiteBrief(
        website_id=website.id,
        business_type=business_type,
        description=description,
        audience=audience or None,
        goals=goals or None,
        style=style or "modern",
    )

    db.session.add(brief)
    db.session.commit()

    return redirect(
        url_for(
            "builder.generation",
            website_id=website.id,
        )
    )


@builder_bp.route("/generation/<int:website_id>")
@login_required
def generation(website_id):

    website = db.session.get(
        Website,
        website_id,
    )

    if website is None:
        return "Website not found", 404

    if website.project.user_id != current_user.id:
        return "Forbidden", 403

    plan = generate_website_plan(
        website
    )

    content = generate_page_content(
        website
    )

    return render_template(
        "builder/generation.html",
        website=website,
        plan=plan,
        content=content,
    )


@builder_bp.route(
    "/generation/<int:website_id>/save",
    methods=["POST"],
)
@login_required
def save_generation(website_id):

    website = db.session.get(
        Website,
        website_id,
    )

    if website is None:
        return "Website not found", 404

    if website.project.user_id != current_user.id:
        return "Forbidden", 403

    plan = generate_website_plan(
        website
    )

    content = generate_page_content(
        website
    )

    save_generated_website(
        website=website,
        plan=plan,
        content=content,
    )

    return redirect(
        url_for(
            "builder.editor",
            website_id=website.id,
        )
    )


@builder_bp.route(
    "/editor/<int:website_id>"
)
@login_required
def editor(website_id):

    website = db.session.get(
        Website,
        website_id,
    )

    if website is None:
        return "Website not found", 404

    if website.project.user_id != current_user.id:
        return "Forbidden", 403

    pages = (
        Page.query
        .filter_by(
            website_id=website.id
        )
        .order_by(Page.id)
        .all()
    )

    return render_template(
        "builder/editor.html",
        website=website,
        pages=pages,
    )


@builder_bp.route(
    "/editor/<int:website_id>/save",
    methods=["POST"],
)
@login_required
def save_editor(website_id):

    website = db.session.get(
        Website,
        website_id,
    )

    if website is None:
        return "Website not found", 404

    if website.project.user_id != current_user.id:
        return "Forbidden", 403

    pages = (
        Page.query
        .filter_by(
            website_id=website.id
        )
        .order_by(Page.id)
        .all()
    )

    for page in pages:

        section_ids = request.form.getlist(
            f"section_id_{page.id}"
        )

        for section_id in section_ids:

            section = db.session.get(
                Section,
                int(section_id),
            )

            if section is None:
                continue

            if section.page_id != page.id:
                continue

            content = dict(
                section.content or {}
            )

            for key in content:

                form_key = (
                    f"section_{section.id}_{key}"
                )

                if form_key not in request.form:
                    continue

                content[key] = request.form.get(
                    form_key,
                    "",
                )

            section.content = content

        latest_version = (
            PageVersion.query
            .filter_by(page_id=page.id)
            .order_by(
                PageVersion.version_number.desc()
            )
            .first()
        )

        next_version = (
            latest_version.version_number + 1
            if latest_version
            else 1
        )

        snapshot = {
            "page": {
                "title": page.title,
                "slug": page.slug,
                "status": page.status,
                "is_homepage": page.is_homepage,
            },
            "sections": [
                {
                    "id": section.id,
                    "type": section.section_type,
                    "position": section.position,
                    "content": section.content,
                    "styles": section.styles,
                }
                for section in page.sections
            ],
        }

        version = PageVersion(
            page_id=page.id,
            version_number=next_version,
            snapshot=snapshot,
        )

        db.session.add(version)

    db.session.commit()

    return redirect(
        url_for(
            "builder.editor",
            website_id=website.id,
        )
    )