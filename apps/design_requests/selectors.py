"""Read-only queries for design requests."""

from apps.design_requests.models import DesignRequest


def design_request_list(*, status=None, client=None):
    qs = DesignRequest.objects.select_related('client').all()
    if status:
        qs = qs.filter(status=status)
    if client is not None:
        qs = qs.filter(client=client)
    return qs


def open_requests():
    return design_request_list(status=DesignRequest.Status.OPEN)


def design_request_get(*, request_id):
    return (
        DesignRequest.objects.select_related('client')
        .prefetch_related('reference_images')
        .get(id=request_id)
    )


def reference_image_get(*, design_request, image_id):
    return design_request.reference_images.get(id=image_id)
