# CLAUDE.md

Development guide for the Jawak backend. Read this before writing code in this repo.

## Stack

- Django 6.0 + Django REST Framework
- PostgreSQL (Neon, via `psycopg2-binary`)
- Config via `.env` (`python-dotenv`), loaded in `core/settings.py`

## Architecture

`core/` is the central project package: settings, root URL conf, WSGI/ASGI entrypoints. It contains **no business logic, no models, no views**.

All feature/business logic lives under `apps/`, one Django app per module/domain (e.g. `apps/user/`, `apps/order/`). Each app is self-contained: its own models, serializers, views, urls, admin, and migrations.

```
jawak_backend/
├── core/
│   ├── settings.py
│   ├── urls.py           # root URLconf — includes each app's urls under /api/v1/<app>/
│   ├── asgi.py / wsgi.py
├── apps/
│   ├── __init__.py
│   ├── user/
│   │   ├── __init__.py
│   │   ├── apps.py       # name = "apps.user"
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── migrations/
│   └── <other_app>/
├── manage.py
├── requirements.txt
├── CLAUDE.md
└── Instructions.md
```

### Adding a new app

1. `python manage.py startapp <name> apps/<name>`
2. In `apps/<name>/apps.py`, set `name = "apps.<name>"` (required since the app lives under `apps/`, not at project root).
3. Register it in `INSTALLED_APPS` in `core/settings.py` as `"apps.<name>"`.
4. Give the app its own `urls.py` with an `app_name` and a `urlpatterns` list.
5. Wire it into `core/urls.py` under a versioned prefix: `path("api/v1/<name>/", include("apps.<name>.urls"))`.
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
- Keep view logic thin — push reusable query/business logic into model managers or serializer `validate`/`create`/`update` methods, not into the view body.

### Settings & config

- All secrets/environment-specific values go in `.env`, read via `os.getenv(...)` in `core/settings.py`. Never hardcode secrets in code.
- `.env` is already gitignored-sensitive data (DB credentials, secret key) — don't print or log its contents.

### Migrations

- Commit migration files alongside the model changes that generated them.
- Don't hand-edit migration files unless resolving a conflict; regenerate instead.

## Instructions.md workflow

`Instructions.md` (repo root) is the running development log/guide for this project. Update it as follows:

- **After finishing a task or adding/changing a module**, add or update a section describing: what was built, where (files/apps touched), the API endpoints created (method + path), what each does, and how the request flow works (view → serializer → model, auth/permissions involved, etc.).
- **Do not** add entries for pure bug fixes or minor revisions with no new functionality.
- **When a later task changes previously documented behavior**, edit the existing section to reflect the new state — don't append a second, conflicting entry for the same feature. `Instructions.md` should always describe the current state of the system, not a chronological diff log (that's what git history is for).
