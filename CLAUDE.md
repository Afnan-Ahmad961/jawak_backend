# CLAUDE.md

Development guide for the Jawak backend. Read this before writing code in this repo.

## What this is

Jawak is a bid-based marketplace for local clothing manufacturing in Pakistan — an "Upwork for garment production." **Clients** (B2C/B2B) post custom apparel requests (hoodies, jackets, football kits, etc.) with designs/specs; **Vendors** (manufacturers) bid on them with price + delivery timeline; the client awards a bid, which becomes an order tracked to completion, then reviewed. **Admins** handle disputes, commissions, and analytics. Auth is via Google OAuth, exchanged for internal JWTs.

Domain model (built incrementally, one app per domain): `User` (`apps/user`) → `VendorProfile` (`apps/vendors`) → `DesignRequest` (`apps/design_requests`, client job posting) → `Bid` (`apps/bids`, vendor proposal) → `Order` (awarded bid) → `Review`. Everything through `Bid` exists; `Order`/`Review` are not built yet. (The requests app is named `design_requests` because `requests` collides with the `requests` library; its URLs are still mounted at `/api/v1/requests/`.)

## Stack

- Django 6.0 + Django REST Framework
- PostgreSQL (Neon, via `psycopg2-binary`)
- Auth: `django-allauth` + `dj-rest-auth` for Google OAuth, `djangorestframework-simplejwt` for JWTs
- File uploads: `django-storages` + `boto3` (S3) with `Pillow` for images; falls back to local media when AWS env vars are unset
- Config via `.env` (`python-dotenv`), loaded in `config/settings/base.py`

## Architecture

`config/` is the central project package: settings, root URL conf, WSGI/ASGI entrypoints. It contains **no business logic, no models, no views**.

Settings are split by environment under `config/settings/`:
- `base.py` — everything common to all environments (installed apps, middleware, database, templates, i18n, etc.). Reads secrets from `.env`.
- `development.py` — `from .base import *`, then `DEBUG = True` and local `ALLOWED_HOSTS`. Default for `manage.py`.
- `production.py` — `from .base import *`, then `DEBUG = False`, env-driven `ALLOWED_HOSTS` (`DJANGO_ALLOWED_HOSTS`), and security hardening (SSL redirect, secure cookies, HSTS). Default for `wsgi.py` / `asgi.py`.

Select the settings module via `DJANGO_SETTINGS_MODULE` (e.g. `config.settings.production`). Shared config goes in `base.py`; environment-specific overrides go in the matching module.

All feature/business logic lives under `apps/`, one Django app per module/domain (e.g. `apps/user/`, `apps/order/`). Each app is self-contained: its own models, serializers, views, urls, admin, and migrations.

```
jawak_backend/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py           # root URLconf — includes each app's urls under /api/v1/<app>/
│   ├── asgi.py / wsgi.py
├── apps/
│   ├── __init__.py
│   ├── user/            # custom User + Google-OAuth-to-JWT auth
│   ├── vendors/         # VendorProfile
│   ├── design_requests/ # DesignRequest (mounted at /api/v1/requests/)
│   ├── bids/            # Bid
│   └── <app>/
│       ├── __init__.py
│       ├── apps.py       # name = "apps.<app>"
│       ├── models.py
│       ├── serializers.py
│       ├── selectors.py  # read operations
│       ├── services.py   # write operations / business logic
│       ├── views.py
│       ├── urls.py
│       ├── admin.py
│       └── migrations/
├── media/               # local uploaded files in dev (gitignored)
├── manage.py
├── requirements.txt
├── CLAUDE.md
└── Instructions.md
```

### Adding a new app

1. `python manage.py startapp <name> apps/<name>`
2. In `apps/<name>/apps.py`, set `name = "apps.<name>"` (required since the app lives under `apps/`, not at project root).
3. Register it in `INSTALLED_APPS` in `config/settings/base.py` as `"apps.<name>"`.
4. Give the app its own `urls.py` with an `app_name` and a `urlpatterns` list.
5. Wire it into `config/urls.py` under a versioned prefix: `path("api/v1/<name>/", include("apps.<name>.urls"))`.
6. Run `python manage.py makemigrations <name>` after adding models.

### URL conventions

- All API routes are versioned: `/api/v1/...`.
- List/create on the collection endpoint: `/api/v1/<resource>/`.
- Retrieve/update/delete on the detail endpoint: `/api/v1/<resource>/<id>/`.
- Use DRF `routers` for straightforward ViewSet-based CRUD; use explicit `path()` entries in the app's `urls.py` for anything custom (actions, non-CRUD endpoints).

### Views, serializers, mixins

- Always go through a serializer for request/response data — no hand-built dicts for model data.
- No fixed rule on class-based vs function-based views; pick whichever is clearest for the endpoint:
  - Standard CRUD over a model → DRF generic views/mixins (`generics.ListCreateAPIView`, `generics.RetrieveUpdateDestroyAPIView`, etc.) or a `ModelViewSet` with a router.
  - Custom/non-CRUD logic (auth flows, actions, aggregation) → `APIView` or a function view with `@api_view`, whichever reads cleaner.
- Prefer composing DRF's mixins/generics over duplicating list/create/retrieve/update/delete logic by hand.
- Keep view logic thin — push reusable query/business logic into services/selectors (below), not into the view body.

### Service & selector pattern

Business logic lives in two per-app modules, so views stay thin and logic is reusable/testable:

- **`services.py`** — write operations. Functions take keyword-only args (`def bid_place(*, vendor, design_request, ...)`), enforce business rules, call `full_clean()`, and save. Multi-step writes wrap in `@transaction.atomic` (see `apps/bids/services.py: bid_accept`).
- **`selectors.py`** — read operations. Functions return querysets/objects with the right `select_related`, filtering, and access scoping.

Views: authenticate/authorize, validate input with a serializer, call a service (write) or selector (read), then serialize the result. Serializers are for validation + representation only — they don't perform writes. Services raise `django.core.exceptions.ValidationError`; views catch it and re-raise as DRF `ValidationError` for a proper 400.

### Auth & permissions

- Custom user model is `apps.user.User` (`AUTH_USER_MODEL = 'user.User'`). It extends `AbstractUser`, logs in by `email`, and adds `role` (`client`/`vendor`/`admin` via `User.Role`), `google_uid`, and `created_at`. Vendor-specific data lives on `apps.vendors.VendorProfile` (OneToOne to `User`, `user.vendor_profile`).
- Sign-in is Google OAuth only: the frontend gets a Google token and POSTs it to `/api/v1/user/auth/google/`, which returns internal JWTs (access + refresh). Authenticate API calls with the JWT `Authorization: Bearer <access>` header.
- DRF defaults (set in `base.py`): `JWTAuthentication`, `IsAuthenticated` for every endpoint, and anon/user rate throttles. Endpoints that should be public must opt out explicitly with `permission_classes = [AllowAny]`. Use `IsAdminUser` / role checks for privileged actions.

### Settings & config

- All secrets/environment-specific values go in `.env`, read via `os.getenv(...)` in `config/settings/base.py`. Never hardcode secrets in code.
- `.env` is already gitignored-sensitive data (DB credentials, secret key) — don't print or log its contents.

### Migrations

- Commit migration files alongside the model changes that generated them.
- Don't hand-edit migration files unless resolving a conflict; regenerate instead.

## Instructions.md workflow

`Instructions.md` (repo root) is the running development log/guide for this project. Update it as follows:

- **After finishing a task or adding/changing a module**, add or update a section describing: what was built, where (files/apps touched), the API endpoints created (method + path), what each does, and how the request flow works (view → serializer → model, auth/permissions involved, etc.).
- **Do not** add entries for pure bug fixes or minor revisions with no new functionality.
- **When a later task changes previously documented behavior**, edit the existing section to reflect the new state — don't append a second, conflicting entry for the same feature. `Instructions.md` should always describe the current state of the system, not a chronological diff log (that's what git history is for).
