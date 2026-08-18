"""
Development settings.

Loaded by default via manage.py. Never use these in production: DEBUG is on
and ALLOWED_HOSTS is limited to local hosts.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# Bare hostnames only — no scheme, no port. This is the Host header Django
# receives (the API runs on :8000), not the frontend's origin.
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', '0.0.0.0']
