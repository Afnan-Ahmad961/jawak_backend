"""
Production settings.

Loaded by default via wsgi.py / asgi.py. DEBUG is off and ALLOWED_HOSTS is
driven by the environment. Set `DJANGO_ALLOWED_HOSTS` to a comma-separated
list of the hostnames this deployment serves.
"""

import os

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]

# Security hardening. These assume the app is served over HTTPS behind a
# proxy/load balancer that sets X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
