"""Read-only queries for vendor profiles."""

from apps.vendors.models import PortfolioItem, VendorProfile


def _base_qs():
    return VendorProfile.objects.select_related('user').prefetch_related(
        'portfolio_items'
    )


def vendor_list():
    return _base_qs().all()


def vendor_get(*, vendor_id):
    return _base_qs().get(id=vendor_id)


def vendor_get_for_user(*, user):
    """Return the caller's own profile, or None if they don't have one."""
    return _base_qs().filter(user=user).first()


def vendors_matching(*, design_request):
    """Vendors whose specialties match the request's apparel type.

    Best-effort token match done in Python (vendor volumes are small): a
    vendor matches if any of their free-text specialties contains the
    apparel type or its human label. Feeds the smart-bidding notifications.
    """
    apparel = design_request.apparel_type
    label = design_request.get_apparel_type_display().lower()
    keyword = apparel.replace('_', ' ')

    matches = []
    for vendor in VendorProfile.objects.select_related('user').all():
        specs = [str(spec).lower() for spec in (vendor.specialties or [])]
        if any(apparel in s or keyword in s or label in s for s in specs):
            matches.append(vendor)
    return matches


def portfolio_item_get(*, vendor, item_id):
    return PortfolioItem.objects.get(id=item_id, vendor=vendor)
