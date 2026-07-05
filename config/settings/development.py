"""
Development settings.

Loaded by default via manage.py. Never use these in production: DEBUG is on
and ALLOWED_HOSTS is limited to local hosts.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
