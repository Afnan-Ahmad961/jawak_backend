"""Write operations (business logic) for design requests."""

from apps.design_requests.models import DesignRequest


def design_request_create(
    *,
    client,
    title,
    apparel_type,
    quantity,
    description='',
    material='',
    design_image=None,
):
    design_request = DesignRequest(
        client=client,
        title=title,
        apparel_type=apparel_type,
        quantity=quantity,
        description=description,
        material=material,
        design_image=design_image,
    )
    design_request.full_clean()
    design_request.save()
    return design_request


def design_request_update(*, design_request, data):
    editable_fields = [
        'title',
        'description',
        'apparel_type',
        'quantity',
        'material',
        'design_image',
    ]
    for field in editable_fields:
        if field in data:
            setattr(design_request, field, data[field])
    design_request.full_clean()
    design_request.save()
    return design_request


def design_request_delete(*, design_request):
    design_request.delete()
