"""Write operations (business logic) for vendor profiles."""

from django.core.exceptions import ValidationError

from apps.vendors.models import VendorProfile


def vendor_profile_create(
    *,
    user,
    company_name,
    location='',
    specialties=None,
    capacity=None,
):
    if VendorProfile.objects.filter(user=user).exists():
        raise ValidationError('A vendor profile already exists for this user.')

    profile = VendorProfile(
        user=user,
        company_name=company_name,
        location=location,
        specialties=specialties or [],
        capacity=capacity,
    )
    profile.full_clean()
    profile.save()

    # Creating a manufacturer profile makes this account a vendor.
    if user.role != user.Role.VENDOR:
        user.role = user.Role.VENDOR
        user.save(update_fields=['role'])

    return profile


def vendor_profile_update(*, profile, data):
    editable_fields = ['company_name', 'location', 'specialties', 'capacity']
    for field in editable_fields:
        if field in data:
            setattr(profile, field, data[field])
    profile.full_clean()
    profile.save()
    return profile
