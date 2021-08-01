from sanic import Blueprint, response
from sanic.exceptions import abort
from sanic.log import logger
from sanic_openapi import doc

from .. import models, settings, utils

blueprint = Blueprint("Shortcuts", url_prefix="/")


@blueprint.get("/images/<template_id>")
@doc.summary("Redirect to an example image")
@doc.consumes(doc.String(name="template_id"), location="path")
@doc.response(
    302, doc.File(), description="Successfully redirected to an example image"
)
@doc.response(404, str, description="Template not found")
@doc.response(501, str, description="Template not fully implemented")
async def example(request, template_id):
    if settings.DEBUG:
        template = models.Template.objects.get_or_create(template_id)
    else:
        template = models.Template.objects.get_or_none(template_id)

    if template and template.valid:
        url = template.build_example_url(
            request.app, "Shortcuts.custom", external=False
        )
        return response.redirect(url)

    if settings.DEBUG:
        if "<" in template_id:
            message = f"Replace {template_id!r} in the URL"
        else:
            message = f"Template not fully implemented: {template}"
            logger.warning(message)
            template.datafile.save()
        abort(501, message)

    abort(404, f"Template not found: {template_id}")


@blueprint.get("/<template_id:ext:png|jpg>")
@doc.exclude(settings.DEPLOYED)
@doc.summary(settings.PREFIX + "Redirect to an example image")
@doc.consumes(doc.String(name="template_id"), location="path")
@doc.response(
    302, doc.File(), description="Successfully redirected to an example image"
)
@doc.response(404, str, description="Template not found")
async def example_ext(request, template_id, ext):
    template = models.Template.objects.get_or_none(template_id)
    if template:
        url = template.build_example_url(request.app, ext=ext, external=False)
        return response.redirect(url)
    abort(404, f"Template not found: {template_id}")


@blueprint.get("/<template_id>")
@doc.exclude(settings.DEPLOYED)
@doc.summary(settings.PREFIX + "Redirect to an example image")
@doc.consumes(doc.String(name="template_id"), location="path")
@doc.response(
    302, doc.File(), description="Successfully redirected to an example image"
)
async def example_legacy(request, template_id):
    return response.redirect(f"/images/{template_id}")


@blueprint.get(r"/images/<template_id>/<text_paths:[\\s\\S]+>")
@doc.summary("Redirect to a custom image")
@doc.consumes(doc.String(name="text_paths"), location="path")
@doc.consumes(doc.String(name="template_id"), location="path")
@doc.produces(
    str,
    description="Successfully displayed a custom meme",
    content_type="text/html",
)
@doc.response(302, doc.File(), description="Successfully redirected to a custom image")
async def custom(request, template_id, text_paths):
    if not settings.DEBUG:
        url = request.app.url_for(
            "Memes.text",
            template_id=template_id,
            text_paths=text_paths.replace("\\", "~b"),
            ext=settings.DEFAULT_EXT,
        )
        return response.redirect(url)

    template = models.Template.objects.get_or_create(template_id)
    template.datafile.save()
    content = utils.html.gallery(
        [f"/images/{template_id}/{text_paths}.png"],
        columns=False,
        refresh=3,
        query_string=request.query_string,
    )
    return response.html(content)


@blueprint.get("/<template_id>/<text_paths:ext:png|jpg>")
@doc.exclude(settings.DEPLOYED)
@doc.summary(settings.PREFIX + "Redirect to a custom image")
@doc.consumes(doc.String(name="text_paths"), location="path")
@doc.consumes(doc.String(name="template_id"), location="path")
@doc.response(302, doc.File(), description="Successfully redirected to a custom image")
@doc.response(404, str, description="Template not found")
async def custom_png(request, template_id, text_paths, ext):
    template = models.Template.objects.get_or_none(template_id)
    if template:
        url = request.app.url_for(
            "Memes.text",
            template_id=template_id,
            text_paths=text_paths,
            ext=ext,
        )
        return response.redirect(url)
    abort(404, f"Template not found: {template_id}")


@blueprint.get(r"/<template_id>/<text_paths:[\\s\\S]+>")
@doc.exclude(settings.DEPLOYED)
@doc.summary(settings.PREFIX + "Redirect to a custom image")
@doc.consumes(doc.String(name="text_paths"), location="path")
@doc.consumes(doc.String(name="template_id"), location="path")
@doc.response(302, doc.File(), description="Successfully redirected to a custom image")
async def custom_legacy(request, template_id, text_paths):
    return response.redirect(f"/images/{template_id}/{text_paths}")
