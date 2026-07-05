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

Business logic follows the **service/selector pattern**: each app keeps write operations in `services.py` (keyword-only functions that enforce rules, `full_clean()`, and save) and read operations in `selectors.py` (scoped querysets). Views authenticate, validate with a serializer, call a service/selector, and serialize the result — they hold no business logic.

## User & Authentication (`apps/user/`)

The user domain: a custom user model, Google-OAuth-to-JWT sign-in, and project-wide DRF auth/permission/throttling defaults.

### Model
- **`User`** (`AUTH_USER_MODEL = 'user.User'`) — extends `AbstractUser`. Logs in by `email` (unique). Adds `role` (`client`/`vendor`/`admin`, default `client`, via `User.Role`), `google_uid` (unique, nullable — the Google account subject id), and `created_at`. Convenience props `is_client` / `is_vendor`. (Vendor details live on `VendorProfile` in `apps/vendors/`.)

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
| GET | `me/` | authenticated | Return the current user (id, email, role, etc.). |

### Config / env
Requires `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `GOOGLE_OAUTH_CALLBACK_URL` in `.env` (credentials from the Google Cloud Console; the callback URL must be registered there). `SITE_ID = 1` and the allauth `AccountMiddleware` are configured in `base.py`.

## Vendors (`apps/vendors/`)

Manufacturer profiles that clients compare when reviewing bids.

### Model
- **`VendorProfile`** — OneToOne to `User` (`user.vendor_profile`). Fields: `company_name`, `location`, `specialties` (JSON list, e.g. `["hoodies", "jackets"]`), `capacity` (units/month), `created_at`, `updated_at`. Creating a profile promotes the user's `role` to `vendor` (in `services.vendor_profile_create`).

### Endpoints (mounted at `/api/v1/vendors/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` (list) | authenticated | Browse all vendor profiles. |
| POST | `me/` | authenticated | Create the caller's own vendor profile (one per user). |
| GET | `me/` | authenticated | Get the caller's own profile (404 if none). |
| PUT/PATCH | `me/` | owner | Update the caller's own profile. |
| GET | `<id>/` | authenticated | Retrieve a specific vendor profile. |

## Design Requests (`apps/design_requests/`)

Client job postings that vendors bid on. App is named `design_requests` (the name `requests` is reserved by the `requests` library) but mounted at `/api/v1/requests/`.

### Model
- **`DesignRequest`** — FK `client` → `User` (`user.design_requests`). Fields: `title`, `description`, `apparel_type` (`hoodie`/`jacket`/`tshirt`/`football_kit`/`other`), `quantity`, `material`, `design_image` (uploaded to cloud/local storage), `status` (`open`/`awarded`/`closed`/`cancelled`, default `open`), `created_at`, `updated_at`. `status` is driven by the bidding flow, not set directly.

### Endpoints (mounted at `/api/v1/requests/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` (list) | authenticated | Clients see their own requests; other roles see the open board. Supports `?status=`. |
| POST | `` | authenticated | Create a request (owner becomes `client`). Accepts multipart for `design_image`. |
| GET | `<id>/` | authenticated | Retrieve a request. |
| PUT/PATCH | `<id>/` | owner/staff | Update a request (multipart supported). |
| DELETE | `<id>/` | owner/staff | Delete a request. |

Image uploads use DRF's `MultiPartParser`; the file is stored via the configured storage backend and exposed as `design_image` (a URL).

## Bids (`apps/bids/`)

Vendor proposals on design requests, and the accept/reject flow.

### Model
- **`Bid`** — FK `design_request` → `DesignRequest` (`design_request.bids`), FK `vendor` → `VendorProfile` (`vendor.bids`). Fields: `proposed_price` (decimal), `delivery_days`, `message`, `status` (`pending`/`accepted`/`rejected`/`withdrawn`, default `pending`), `created_at`, `updated_at`. Unique constraint on (`design_request`, `vendor`) — one bid per vendor per request.

### Business rules (`services.py`)
- **`bid_place`** — rejects bids on requests that aren't `open`; `full_clean` enforces the one-bid-per-vendor rule.
- **`bid_accept`** (atomic) — sets the bid `accepted`, marks all sibling bids `rejected`, and sets the request `awarded`. Only allowed while the request is still `open`.
- **`bid_reject`** — sets a single bid `rejected`.

### Endpoints (mounted at `/api/v1/bids/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| POST | `` | vendor (has profile) | Place a bid on a request. |
| GET | `?request=<id>` | request owner/staff (all) or vendor (own) | List bids for a request. |
| GET | `` (no param) | authenticated | List the caller-vendor's own bids. |
| GET | `<id>/` | request owner, bidding vendor, or staff | Retrieve a bid. |
| PATCH | `<id>/status/` | request owner/staff | Accept or reject the bid (`{"status": "accepted"|"rejected"}`). |

## File storage (`django-storages` + S3)

Uploaded files (currently design images) are handled by `django-storages`. When `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_STORAGE_BUCKET_NAME` are set in `.env`, the default `STORAGES` backend is S3 (`storages.backends.s3.S3Storage`, `AWS_S3_REGION_NAME` optional); otherwise it falls back to local `FileSystemStorage` under `MEDIA_ROOT` (`media/`, gitignored, served at `/media/` in DEBUG). No cloud setup is needed to run locally.
