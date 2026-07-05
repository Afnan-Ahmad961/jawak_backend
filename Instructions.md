# Instructions.md

This is the living development guide for the Jawak backend. It describes the current state of the system: what modules exist, what each API endpoint does, and how the request flow works for each. It is updated after every completed task or new module — not for bug fixes or minor revisions. When a feature changes, the relevant section below is revised in place rather than appended to.

See [CLAUDE.md](CLAUDE.md) for the architecture conventions this project follows.

## Product overview

Jawak is a bid-based marketplace for local clothing manufacturing in Pakistan. Clients post custom apparel requests (designs + specs); vendors (manufacturers) bid with price and delivery timeline; the client awards a bid, which becomes a tracked order and is reviewed on completion. Admins manage disputes, commissions, and analytics. The planned domain progression is `User`/`VendorProfile` → `Request` → `Bid` → `Order` → `Review`. See `project-details.txt` for the full plan.

## Project bootstrap

Django 6.0 project with `config` as the central project package (settings, root URL conf, WSGI/ASGI). DRF is installed. Database is PostgreSQL hosted on Neon, configured entirely through environment variables in `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) and read in `config/settings/base.py` via `python-dotenv`. `SECRET_KEY` is environment-driven.

Settings are split by environment under `config/settings/`:
- `base.py` holds all shared config (installed apps, middleware, database, templates, i18n, static, auth validators) and loads `.env`.
- `development.py` imports base, sets `DEBUG = True`, and limits `ALLOWED_HOSTS` to local hosts. It is the default settings module for `manage.py`.
- `production.py` imports base, sets `DEBUG = False`, reads `ALLOWED_HOSTS` from `DJANGO_ALLOWED_HOSTS`, and enables security hardening (SSL redirect, secure/HSTS cookies). It is the default for `wsgi.py` / `asgi.py`.

The active module is chosen with `DJANGO_SETTINGS_MODULE` (e.g. `config.settings.production` in deployment).

The `apps/` package holds all feature apps. New modules are added under `apps/<name>/` per the convention in CLAUDE.md, each with its own models, serializers, views, and urls, mounted in `config/urls.py` under `/api/v1/<name>/`.

## User & Authentication (`apps/user/`)

The user domain: a custom user model, Google-OAuth-to-JWT sign-in, and project-wide DRF auth/permission/throttling defaults.

### Models
- **`User`** (`AUTH_USER_MODEL = 'user.User'`) — extends `AbstractUser`. Logs in by `email` (unique). Adds `role` (`client`/`vendor`/`admin`, default `client`, via `User.Role`), `google_uid` (unique, nullable — the Google account subject id), and `created_at`. Convenience props `is_client` / `is_vendor`.
- **`VendorProfile`** — OneToOne to `User`. Fields: `company_name`, `location`, `specialties` (JSON list, e.g. `["hoodies", "jackets"]`), `capacity` (units/month), `created_at`. Accessible as `user.vendor_profile`.

### Auth flow
Sign-in is Google OAuth only. The frontend obtains a Google access token/code and POSTs it to the Google login endpoint; `dj-rest-auth` + `django-allauth` verify it, create-or-fetch the matching `User`, and return internal JWTs from `djangorestframework-simplejwt`. Subsequent API calls send `Authorization: Bearer <access>`.

### DRF defaults (`config/settings/base.py`)
- Authentication: `JWTAuthentication` (+ `SessionAuthentication` for the browsable API/admin).
- Permission: `IsAuthenticated` on every endpoint by default — public endpoints must opt out with `AllowAny`.
- Throttling: `AnonRateThrottle` / `UserRateThrottle`, rates from `THROTTLE_ANON` (default `30/min`) and `THROTTLE_USER` (default `120/min`).
- JWT lifetimes: 60-min access, 7-day refresh (rotating).

### Endpoints (mounted at `/api/v1/user/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| POST | `auth/google/` | public | Exchange a Google token (`access_token` or `code`) for internal JWTs; creates the user on first login. |
| POST | `auth/token/refresh/` | public (valid refresh) | Get a new access token from a refresh token. |
| POST | `auth/token/verify/` | public | Verify a token is valid. |
| POST | `auth/logout/` | authenticated | Log out (blacklist/clear refresh). |
| GET | `me/` | authenticated | Return the current user, including `vendor_profile` when present. |

### Config / env
Requires `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `GOOGLE_OAUTH_CALLBACK_URL` in `.env` (credentials from the Google Cloud Console; the callback URL must be registered there). `SITE_ID = 1` and the allauth `AccountMiddleware` are configured in `base.py`.
