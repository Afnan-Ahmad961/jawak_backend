"""Write operations (business logic) for design requests."""

from apps.design_requests.models import DesignReferenceImage, DesignRequest


def design_request_create(
    *,
    client,
    title,
    apparel_type,
    quantity,
    description='',
    material='',
    sizes=None,
    color_preferences='',
    deadline=None,
    design_image=None,
):
    design_request = DesignRequest(
        client=client,
        title=title,
        apparel_type=apparel_type,
        quantity=quantity,
        description=description,
        material=material,
        sizes=sizes or [],
        color_preferences=color_preferences,
        deadline=deadline,
        design_image=design_image,
    )
    design_request.full_clean()
    design_request.save()

    # Smart bidding: alert vendors whose specialties match this request.
    from apps.notifications.services import notify_many
    from apps.vendors.selectors import vendors_matching

    matches = vendors_matching(design_request=design_request)
    notify_many(
        recipients=[vendor.user for vendor in matches],
        notification_type='matching_request',
        message=f'New {design_request.get_apparel_type_display()} request: '
        f'"{design_request.title}".',
        target=design_request,
    )
    return design_request


def design_request_update(*, design_request, data):
    editable_fields = [
        'title',
        'description',
        'apparel_type',
        'quantity',
        'material',
        'sizes',
        'color_preferences',
        'deadline',
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


def reference_image_add(*, design_request, image, label=''):
    reference = DesignReferenceImage(
        design_request=design_request, image=image, label=label
    )
    reference.full_clean()
    reference.save()
    return reference


def reference_image_delete(*, reference):
    reference.delete()
