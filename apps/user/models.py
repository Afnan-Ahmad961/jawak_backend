from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model.

    Extends Django's AbstractUser (keeping username/password and the
    is_staff/is_superuser flags) and adds a marketplace `role` plus fields
    used for Google OAuth sign-in. Email is unique and used as the login
    identifier.
    """

    class Role(models.TextChoices):
        CLIENT = 'client', 'Client'
        VENDOR = 'vendor', 'Vendor'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    # Google account subject id ("sub"). Null for accounts that never used
    # Google sign-in; unique so a Google account maps to exactly one user.
    google_uid = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f'{self.email} ({self.role})'

    @property
    def is_vendor(self):
        return self.role == self.Role.VENDOR

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT
