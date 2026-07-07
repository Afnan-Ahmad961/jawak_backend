# Instructions.md

This is the living development guide for the Jawak backend. It describes the current state of the system: what modules exist, what each API endpoint does, and how the request flow works for each. It is updated after every completed task or new module — not for bug fixes or minor revisions. When a feature changes, the relevant section below is revised in place rather than appended to.

See [CLAUDE.md](CLAUDE.md) for the architecture conventions this project follows.

## Product overview

Jawak is a bid-based marketplace for local clothing manufacturing in Pakistan. Clients post custom apparel requests (designs + specs); vendors (manufacturers) bid with price and delivery timeline; the client awards a bid, which becomes a tracked order and is reviewed on completion. Admins manage disputes and analytics. The full flow is built: `User`/`VendorProfile` → `DesignRequest` → `Bid` → `Order` (+ production tracking) → `Review`, with supporting `Notifications`, `Messaging`, and `Disputes`. **Escrow & secure payments are deferred** — commission/revenue reporting waits for that module. See `IMPLEMENTATION_PLAN.md` for the plan these modules were built from and `project-details.txt` for the original brief.

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

### Models
- **`VendorProfile`** — OneToOne to `User` (`user.vendor_profile`). Fields: `company_name`, `location`, `specialties` (JSON list, e.g. `["hoodies", "jackets"]`), `capacity` (units/month), `avg_rating` / `review_count` (denormalized rating aggregates, recomputed by `apps/reviews` when a review lands), `created_at`, `updated_at`. Creating a profile promotes the user's `role` to `vendor` (in `services.vendor_profile_create`).
- **`PortfolioItem`** — FK `vendor` → `VendorProfile` (`vendor.portfolio_items`). A past-work sample: `image` (validated, see [File storage](#file-storage-django-storages--s3)), `title`, `description`, `created_at`.

Together `avg_rating`, `review_count`, and `portfolio_items` (plus bid price and delivery time) give clients the full **vendor comparison dashboard** — surfaced on the vendor list/detail serializers.

### Matching
`selectors.vendors_matching(design_request)` returns vendors whose free-text `specialties` match the request's apparel type (best-effort token match in Python). It powers the smart-bidding notifications fired from `apps/design_requests`.

### Endpoints (mounted at `/api/v1/vendors/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` (list) | authenticated | Browse all vendor profiles (includes ratings + portfolio). |
| POST | `me/` | authenticated | Create the caller's own vendor profile (one per user). |
| GET | `me/` | authenticated | Get the caller's own profile (404 if none). |
| PUT/PATCH | `me/` | owner | Update the caller's own profile. |
| POST | `me/portfolio/` | vendor (has profile) | Add a portfolio item (multipart image). |
| DELETE | `me/portfolio/<item_id>/` | owner | Remove a portfolio item. |
| GET | `<id>/` | authenticated | Retrieve a specific vendor profile. |

## Design Requests (`apps/design_requests/`)

Client job postings that vendors bid on. App is named `design_requests` (the name `requests` is reserved by the `requests` library) but mounted at `/api/v1/requests/`.

### Models
- **`DesignRequest`** — FK `client` → `User` (`user.design_requests`). Fields: `title`, `description`, `apparel_type` (`hoodie`/`jacket`/`tshirt`/`football_kit`/`other`), `quantity`, `material`, `sizes` (JSON list of size/quantity breakdowns, e.g. `[{"size": "M", "quantity": 20}]`), `color_preferences`, `deadline` (date), `design_image` (validated, uploaded to cloud/local storage), `status` (`open`/`awarded`/`closed`/`cancelled`, default `open`), `created_at`, `updated_at`. `status` is driven by the bidding flow, not set directly.
- **`DesignReferenceImage`** — FK `design_request` → `DesignRequest` (`design_request.reference_images`). Multiple artwork/logo/graphic elements to apply to the article (emblem, sponsor logos, back print, etc.), each with `image` (validated) and optional `label`. Nested read-only on the request; created/deleted via the reference-images endpoints.

### Creation side effect (smart bidding)
`services.design_request_create` fires the **smart-bidding** fan-out: it runs `vendors.selectors.vendors_matching` and sends each matching vendor a `matching_request` notification (see [Notifications](#notifications-appsnotifications)).

### Endpoints (mounted at `/api/v1/requests/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` (list) | authenticated | Clients see their own requests; other roles see the open board. Supports `?status=`. |
| POST | `` | client/staff | Create a request. Accepts multipart for `design_image`. |
| GET | `<id>/` | authenticated | Retrieve a request (with nested `reference_images`). |
| PUT/PATCH | `<id>/` | owner/staff | Update a request (multipart supported). |
| DELETE | `<id>/` | owner/staff | Delete a request. |
| POST | `<id>/reference-images/` | owner/staff | Attach a reference image (multipart). |
| DELETE | `<id>/reference-images/<image_id>/` | owner/staff | Remove a reference image. |

Image uploads use DRF's `MultiPartParser`; files are stored via the configured storage backend and exposed as URLs.

## Bids (`apps/bids/`)

Vendor proposals on design requests, and the accept/reject flow.

### Model
- **`Bid`** — FK `design_request` → `DesignRequest` (`design_request.bids`), FK `vendor` → `VendorProfile` (`vendor.bids`). Fields: `proposed_price` (decimal, min `0.01`), `delivery_days` (min `1`), `message`, `status` (`pending`/`accepted`/`rejected`/`withdrawn`, default `pending`), `created_at`, `updated_at`. Unique constraint on (`design_request`, `vendor`) — one bid per vendor per request.

### Business rules (`services.py`)
- **`bid_place`** — rejects bids on requests that aren't `open`; `full_clean` enforces the one-bid-per-vendor rule; notifies the client of the new bid.
- **`bid_accept`** (atomic) — re-reads the request row with `select_for_update` (so two concurrent accepts can't both win), sets the bid `accepted`, marks all sibling bids `rejected`, sets the request `awarded`, and **creates the `Order`** via `orders.services.order_create_from_bid`. Only allowed while the request is still `open`.
- **`bid_reject`** — sets a single bid `rejected`.
- **`bid_withdraw`** — the bidding vendor withdraws a still-`pending` bid.

### Endpoints (mounted at `/api/v1/bids/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| POST | `` | vendor (has profile) | Place a bid on a request. |
| GET | `?request=<id>` | request owner/staff (all) or vendor (own) | List bids for a request. |
| GET | `` (no param) | authenticated | List the caller-vendor's own bids. |
| GET | `<id>/` | request owner, bidding vendor, or staff | Retrieve a bid. |
| PATCH | `<id>/status/` | request owner/staff | Accept or reject the bid (`{"status": "accepted"|"rejected"}`). Accepting opens an order. |
| POST | `<id>/withdraw/` | bidding vendor | Withdraw a pending bid. |

## Orders & Production Tracking (`apps/orders/`)

The contract created when a bid is accepted, plus the manufacturing timeline the client follows to completion.

### Models
- **`Order`** — created by `order_create_from_bid` inside the `bid_accept` transaction. OneToOne `bid` → `Bid` (`bid.order`); denormalized FKs `design_request`, `vendor`, `client`. Fields: `final_price` (snapshot of the awarded bid price, immutable), `deadline` (derived as today + bid `delivery_days`), `current_stage` (`sourcing`→`cutting`→`sewing`→`quality_check`→`shipped`→`delivered`), `status` (`active`/`completed`/`cancelled`/`disputed`), timestamps. FKs to bid/request/vendor/client use `PROTECT` so an order's inputs can't be deleted out from under it. `Order.STAGE_ORDER` defines the forward-only stage sequence.
- **`ProductionUpdate`** — FK `order` → `Order` (`order.production_updates`). A vendor-posted milestone: `stage`, `note`, optional validated `image`, `created_by`, `created_at`. Forms the client-facing timeline.

### Business rules (`services.py`)
- **`order_create_from_bid`** — snapshots price + deadline, creates the order, notifies the vendor they won (`bid_accepted`). Called only from `bid_accept`.
- **`production_update_add`** (atomic) — vendor posts an update; enforces the order is `active` and the stage does not move backwards; advances `current_stage`; notifies the client (`production_update`).
- **`order_confirm_delivery`** — the client confirms a `delivered` order, flipping it to `completed`, which unlocks reviews.

### Endpoints (mounted at `/api/v1/orders/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` | authenticated | Orders the caller participates in (as client or vendor). Supports `?status=`. |
| GET | `<id>/` | participant/staff | Retrieve an order with its production timeline. |
| POST | `<id>/production-updates/` | assigned vendor | Post a production milestone update (multipart image optional). |
| POST | `<id>/confirm-delivery/` | client | Confirm delivery and complete the order. |

## Reviews (`apps/reviews/`)

Two-way feedback after a completed order.

### Model
- **`Review`** — FK `order`, `reviewer`, `reviewee` (both → `User`), `rating` (1–5), `comment`, `created_at`. Unique on (`order`, `reviewer`) — one review per party per order.

### Business rules (`services.py`)
- **`review_create`** (atomic) — allowed only when the order is `completed` and the reviewer is a participant; derives the `reviewee` as the other party; if the reviewee is a vendor, recomputes that `VendorProfile`'s `avg_rating`/`review_count`; notifies the reviewee (`new_review`).

### Endpoints (mounted at `/api/v1/reviews/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `?vendor=<id>` / `?order=<id>` | authenticated | List reviews, optionally filtered by vendor or order. |
| POST | `` | order participant | Create a review (`order`, `rating`, `comment`). |

## Notifications (`apps/notifications`)

In-app notifications, DB-only and synchronous for now (email/push/WebSocket can layer on later).

### Model
- **`Notification`** — FK `recipient` → `User` (`user.notifications`). Fields: `notification_type` (matching_request / new_bid / bid_accepted / production_update / new_review / new_message / dispute_opened / dispute_resolved), `message`, an optional generic relation (`content_type` + `object_id` → `target`) pointing at whatever the notification is about, `is_read`, `created_at`. The generic relation avoids this app holding a foreign key to every other app.

### Producing notifications (`services.py`)
`notify(...)` / `notify_many(...)` are called **explicitly** from other apps' services at the point the event happens (not via signals), keeping the flow traceable. `notification_mark_read` / `notifications_mark_all_read` handle the read state.

### Endpoints (mounted at `/api/v1/notifications/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` | authenticated | List the caller's notifications. Supports `?unread=true`. |
| POST | `<id>/read/` | recipient | Mark one notification read. |
| POST | `read-all/` | authenticated | Mark all the caller's notifications read. |

## Messaging (`apps/messaging/`)

Negotiation chat between a request's client and a vendor. REST + polling for now.

### Models
- **`Conversation`** — FK `design_request`, FK `vendor`; unique on (`design_request`, `vendor`). Participants are the request's client and the vendor's user.
- **`Message`** — FK `conversation` (`conversation.messages`), FK `sender`, `body`, `is_read`, `created_at`.

### Business rules (`services.py`)
- **`conversation_start`** — get-or-creates the thread; the caller must be one of the two participants.
- **`message_send`** — posts a message, bumps the conversation's `updated_at`, and notifies the other participant (`new_message`).

### Endpoints (mounted at `/api/v1/conversations/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` | participant | List the caller's conversations. |
| POST | `` | participant | Start/open a conversation (`design_request`, `vendor`). |
| GET | `<id>/messages/` | participant | List messages in a conversation. |
| POST | `<id>/messages/` | participant | Send a message. |

## Disputes (`apps/disputes/`)

Complaints on an order, resolved by an admin.

### Model
- **`Dispute`** — FK `order` (`order.disputes`), FK `raised_by`, `reason`, `description`, `status` (`open`/`under_review`/`resolved`/`rejected`), `resolution`, FK `resolved_by` (admin), timestamps.

### Business rules (`services.py`)
- **`dispute_open`** (atomic) — a participant raises a dispute on an `active`/`completed` order; sets the order `disputed`; notifies all admins (`dispute_opened`).
- **`dispute_resolve`** (atomic) — an admin resolves/rejects; records `resolution` + `resolved_by`; returns the order to `active`; notifies the raiser (`dispute_resolved`).

### Endpoints (mounted at `/api/v1/disputes/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `` | admin (all) / participant (own) | List disputes. |
| POST | `` | order participant | Open a dispute (`order`, `reason`, `description`). |
| PATCH | `<id>/` | admin (`is_staff` or `admin` role) | Resolve or reject (`status`, `resolution`). |

## Analytics (`apps/analytics/`)

Admin-only, read-only reporting. No models of its own — it aggregates data owned by the other apps (`selectors.overview`). Revenue/commission metrics are intentionally omitted until the payments module ships.

### Endpoints (mounted at `/api/v1/analytics/`)
| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| GET | `overview/` | admin (`IsAdminUser`) | Totals (requests/bids/orders/vendors/disputes), average bid amount, bids-per-request, dispute rate, requests-by-apparel-type, orders-by-status, and top vendors (rating + completed orders). |

## Shared utilities (`apps/common/`)

A plain utility package (no models, not an installed app). `validators.py` provides `IMAGE_VALIDATORS` — an extension allow-list (`jpg/jpeg/png/webp`), a 5 MB size cap, and a 6000px dimension cap (decompression-bomb guard) — attached to every `ImageField` in the project.

## File storage (`django-storages` + S3)

Uploaded files (design images, reference images, portfolio items, production-update photos) are handled by `django-storages` and validated by `apps.common.validators.IMAGE_VALIDATORS`. When `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_STORAGE_BUCKET_NAME` are set in `.env`, the default `STORAGES` backend is S3 (`storages.backends.s3.S3Storage`, `AWS_S3_REGION_NAME` optional); otherwise it falls back to local `FileSystemStorage` under `MEDIA_ROOT` (`media/`, gitignored, served at `/media/` in DEBUG). No cloud setup is needed to run locally.
