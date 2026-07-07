# Jawak Backend — Overview

A quick, high-level picture of the backend and a frontend integration guide.
For deep per-endpoint detail see [Instructions.md](Instructions.md); for the
build plan see [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

---

## 1. What Jawak is

A bid-based marketplace for local clothing manufacturing ("Upwork for garment
production"). **Clients** post custom apparel requests → **Vendors**
(manufacturers) bid with price + timeline → the client awards a bid → it
becomes a tracked **Order** through production → both parties **review** each
other. **Admins** handle disputes and see analytics.

---

## 2. Architecture at a glance

```
                        ┌─────────────────────────────┐
   Next.js frontend ──▶ │   Django REST API  /api/v1  │
   (Bearer JWT)         └──────────────┬──────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
   Auth & users                 Marketplace core              Support modules
   ───────────                  ───────────────               ───────────────
   user (Google→JWT)   vendors → design_requests → bids       notifications
                                     → orders → reviews        messaging
                                                               disputes
                                                               analytics
                                       │
                              ┌────────┴────────┐
                              │  PostgreSQL      │  (Neon)
                              │  S3 / local media│  (uploads)
                              └──────────────────┘
```

**Stack:** Django 6 + Django REST Framework · PostgreSQL (Neon) · JWT auth
(Google OAuth sign-in) · file uploads to S3 (local media fallback in dev).

**One app per domain.** Each app owns its models, API, and business logic:

| App | Owns |
| :--- | :--- |
| `user` | Accounts, roles (client/vendor/admin), Google-OAuth-to-JWT login |
| `vendors` | Manufacturer profiles, portfolio, ratings, job matching |
| `design_requests` | Client job postings (specs, design + reference images) |
| `bids` | Vendor proposals; accepting one awards the job |
| `orders` | The awarded contract + production-stage timeline |
| `reviews` | Two-way feedback after completion |
| `notifications` | In-app alerts (new bid, production update, etc.) |
| `messaging` | Client ↔ vendor negotiation chat |
| `disputes` | Complaints raised on orders, resolved by admins |
| `analytics` | Admin-only aggregate reporting |

**How a request is handled:** every endpoint authenticates the JWT, checks the
caller's role/ownership, validates the body, runs business logic in a service
(write) or selector (read), and returns serialized JSON. Views stay thin.

**The core lifecycle:**

```
DesignRequest(open) ──bid──▶ Bid(pending) ──accept──▶ Order(active)
        │                         │                        │
   matching vendors          client picks           production updates
   get notified              a winner               sourcing→…→delivered
                                                         │
                                              client confirms delivery
                                                         │
                                                  Order(completed) ──▶ Reviews
```

---

## 3. Frontend integration guide

Base URL: `/api/v1/`. All responses are JSON. All dates are ISO-8601 UTC.

### Authentication (all roles)

Sign-in is **Google OAuth only**. The frontend gets a Google token, exchanges
it for Jawak JWTs, and sends the access token on every call.

1. Get a Google `access_token` (or `code`) via Google Sign-In on the frontend.
2. `POST /api/v1/user/auth/google/` with `{ "access_token": "<google token>" }`
   → returns `{ access, refresh, user }`. The user is created on first login.
3. Send `Authorization: Bearer <access>` on every subsequent request.
4. When the access token expires (60 min), `POST /api/v1/user/auth/token/refresh/`
   with `{ "refresh": "<refresh>" }` → new access token.
5. `GET /api/v1/user/me/` returns the current user, including **`role`** — use
   it to decide which dashboard (customer / vendor / admin) to render.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| POST | `user/auth/google/` | Google token → Jawak JWTs |
| POST | `user/auth/token/refresh/` | Refresh the access token |
| POST | `user/auth/token/verify/` | Check a token is valid |
| POST | `user/auth/logout/` | Log out |
| GET  | `user/me/` | Current user + role |

**Notes for the frontend**
- A new account starts as a **client**. It becomes a **vendor** automatically
  the moment it creates a vendor profile (`POST vendors/me/`).
- File uploads (images) must be sent as `multipart/form-data`, not JSON.
- Notifications are the shared signal across all roles — poll
  `GET notifications/?unread=true` (or on an interval) to drive a badge/bell.

---

### 👤 Customer (Client) flow

The client posts a job, compares bids, awards one, follows production, and
reviews the vendor.

**Journey → endpoints**

1. **Post a request** — `POST requests/` (multipart: title, apparel_type,
   quantity, sizes, color_preferences, deadline, `design_image`). Attach extra
   artwork with `POST requests/<id>/reference-images/`.
2. **Track own requests** — `GET requests/` (clients see their own; `?status=`
   to filter). `GET requests/<id>/` for detail incl. reference images.
3. **Compare bids** — `GET bids/?request=<id>` returns all bids on that request
   with vendor company, price, delivery days. Pull vendor detail
   (`GET vendors/<id>/`) for rating, review count, and portfolio.
4. **Negotiate (optional)** — `POST conversations/` `{design_request, vendor}`
   then `POST conversations/<id>/messages/`.
5. **Award** — `PATCH bids/<id>/status/` `{ "status": "accepted" }`. This
   rejects the other bids and **creates the order** automatically.
6. **Follow production** — `GET orders/` / `GET orders/<id>/` shows
   `current_stage` and the `production_updates` timeline.
7. **Confirm delivery** — `POST orders/<id>/confirm-delivery/` once delivered;
   the order becomes `completed`.
8. **Review** — `POST reviews/` `{ order, rating, comment }`.
9. **Dispute (if needed)** — `POST disputes/` `{ order, reason, description }`.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| POST | `requests/` | Post a new design request |
| GET | `requests/` · `requests/<id>/` | List own / view a request |
| PUT/PATCH · DELETE | `requests/<id>/` | Edit / delete own request |
| POST · DELETE | `requests/<id>/reference-images/` (`/<image_id>/`) | Add / remove artwork |
| GET | `bids/?request=<id>` | Compare bids on a request |
| GET | `vendors/` · `vendors/<id>/` | Browse / inspect vendors |
| PATCH | `bids/<id>/status/` | Accept or reject a bid |
| GET | `orders/` · `orders/<id>/` | Track awarded orders + production |
| POST | `orders/<id>/confirm-delivery/` | Confirm delivery |
| POST | `reviews/` | Review the vendor |
| POST | `disputes/` | Raise a dispute |
| GET/POST | `conversations/` · `conversations/<id>/messages/` | Chat with a vendor |
| GET/POST | `notifications/` … | Alerts (new bids, updates) |

---

### 🏭 Vendor (Manufacturer) flow

The vendor sets up a profile, discovers matching jobs, bids, and runs
production once awarded.

**Journey → endpoints**

1. **Create profile** — `POST vendors/me/` (company_name, location,
   specialties, capacity). This promotes the account to **vendor**. Edit with
   `PATCH vendors/me/`.
2. **Build portfolio** — `POST vendors/me/portfolio/` (multipart image, title,
   description); remove with `DELETE vendors/me/portfolio/<item_id>/`.
3. **Discover jobs** — the open board is `GET requests/` (non-clients see all
   open requests; `?status=open`). Vendors whose `specialties` match a new
   request also get a `matching_request` notification automatically.
4. **Bid** — `POST bids/` `{ design_request, proposed_price, delivery_days,
   message }`. One bid per request. Withdraw a pending bid with
   `POST bids/<id>/withdraw/`. Track own bids with `GET bids/` (no param).
5. **Negotiate (optional)** — same `conversations/` endpoints as the client.
6. **Run production (after being awarded)** — `GET orders/` shows assigned
   orders. Post milestones with `POST orders/<id>/production-updates/`
   `{ stage, note, image? }`. Stages go forward only:
   `sourcing → cutting → sewing → quality_check → shipped → delivered`.
7. **Review the client** — after completion, `POST reviews/`.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| POST · GET · PATCH | `vendors/me/` | Create / view / edit own profile |
| POST · DELETE | `vendors/me/portfolio/` (`/<item_id>/`) | Manage portfolio |
| GET | `requests/` · `requests/<id>/` | Browse the open job board |
| POST | `bids/` | Place a bid |
| GET | `bids/` | List own bids |
| POST | `bids/<id>/withdraw/` | Withdraw a pending bid |
| GET | `orders/` · `orders/<id>/` | Assigned orders |
| POST | `orders/<id>/production-updates/` | Post a production milestone |
| POST | `reviews/` | Review the client |
| GET/POST | `conversations/` … | Chat with the client |
| GET/POST | `notifications/` … | Alerts (matching jobs, awards) |

---

### 🛡️ Admin flow

Admins moderate disputes and monitor the marketplace. (Admin = user with the
`admin` role / Django staff.)

**Journey → endpoints**

1. **Review disputes** — `GET disputes/` returns every dispute (participants
   only see their own; admins see all).
2. **Resolve a dispute** — `PATCH disputes/<id>/`
   `{ "status": "resolved" | "rejected", "resolution": "..." }`. Resolving
   returns the affected order to `active` and notifies the person who raised it.
3. **Monitor** — `GET analytics/overview/` returns totals (requests, bids,
   orders, vendors, disputes), average bid amount, bids-per-request, dispute
   rate, requests-by-apparel-type, orders-by-status, and top vendors.

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| GET | `disputes/` | All disputes |
| PATCH | `disputes/<id>/` | Resolve / reject a dispute |
| GET | `analytics/overview/` | Marketplace analytics dashboard |

> **Not yet available:** escrow/payments and commission/revenue reporting are
> deferred, so analytics shows volume metrics only — no money figures yet.

---

## 4. Frontend cheat-sheet

- **Route by role** from `user/me/` → `role`: `client` → customer dashboard,
  `vendor` → vendor dashboard, `admin` → admin console.
- **Always** send `Authorization: Bearer <access>`; refresh on 401.
- **Multipart** for anything with an image (`requests/`, reference-images,
  portfolio, production-updates); JSON for everything else.
- **Statuses to render:**
  - Request: `open → awarded → closed / cancelled`
  - Bid: `pending → accepted / rejected / withdrawn`
  - Order: `active → completed` (or `disputed` / `cancelled`)
  - Production stage: `sourcing → cutting → sewing → quality_check → shipped → delivered`
  - Dispute: `open → under_review → resolved / rejected`
- **Notifications** power live UX across every screen — poll
  `notifications/?unread=true` for the bell, `POST notifications/<id>/read/` or
  `read-all/` to clear.
