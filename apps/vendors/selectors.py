"""Read-only queries for vendor profiles."""

from apps.vendors.models import VendorProfile


def vendor_list():
    return VendorProfile.objects.select_related('user').all()


def vendor_get(*, vendor_id):
    return VendorProfile.objects.select_related('user').get(id=vendor_id)


def vendor_get_for_user(*, user):
    """Return the caller's own profile, or None if they don't have one."""
    return VendorProfile.objects.filter(user=user).select_related('user').first()
