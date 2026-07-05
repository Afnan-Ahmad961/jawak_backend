# Jawak Architecture Overview

## Core Principles

- **One app per domain**: Each logical domain (vendors, design_requests, bids, orders, reviews, notifications, messaging, analytics) is implemented as a separate Django app.
- **Service/Selector Pattern**: Business logic lives in `services.py` (write operations) and `selectors.py` (read operations). Views are thin wrappers that handle auth, validation, and serialization.
- **Service Layer**: Encapsulates business rules, validation, and state transitions. Keeps views lean.
- **Service Layer Pattern**: Write operations live in `services.py` (keyword-only functions), read operations in `selectors.py` (querysets).
- **Service Layer Pattern**: Write operations enforce validation, state transitions, and side effects (notifications, side effects). Read operations provide scoped querysets.

## Core Apps Overview

| App | Responsibility | Key Models |
|-----|----------------|-----------|
| **user** | Authentication, roles (client/vendor/admin), Google OAuth → JWT | `User`, `VendorProfile` |
| **vendors** | Manufacturer profiles, portfolio, ratings | `VendorProfile`, `PortfolioItem` |
| **design_requests** | Client job postings with design specs | `DesignRequest`, `DesignReferenceImage` |
| **bids** | Vendor proposals on design requests | `Bid` |
| **orders** | Awarded contracts and production tracking | `Order`, `ProductionUpdate` |
| **reviews** | Post-completion feedback | `Review` |
| **notifications** | In-app notifications for events | `Notification` |
| **messaging** | Client-vendor chat | `Conversation`, `Message` |
| **disputes** | Dispute resolution for orders | `Dispute` |
| **analytics** | Admin-only aggregate reporting | No models (uses selectors from other apps) |
| **messaging** | Client-vendor chat | `Conversation`, `Message` |

## Core Lifecycle

1. **Design Request Creation** – Client creates a `DesignRequest` with specifications and reference images.
2. **Bidding** – Vendors submit `Bid`s on open requests.
3. **Bid Acceptance** – Client accepts a bid, creating an `Order` and notifying the vendor.
4. **Production Tracking** – Vendor updates order stages via `ProductionUpdate`; client can confirm delivery.
5. **Review & Feedback** – After delivery, both parties can submit `Review`s.
6. **Dispute Resolution** – Any party can open a `Dispute` for unresolved issues; admins resolve it.
7. **Analytics** – Admin can query aggregated metrics via the `analytics` app.

## Core Data Flow

1. **Authentication** – Google OAuth → JWT → `Authorization: Bearer <token>`.
2. **API Access** – All endpoints under `/api/v1/` return JSON; dates are ISO-8601 UTC.
3. **Data Flow** – Views authenticate → validate → call service/selectors → return JSON.
4. **Notifications** – Emitted directly from service layers, not via signals.
5. **File Storage** – Uses `django-storages` + S3; falls back to local `FileSystemStorage` in development.

## Key Conventions

- **JWT Auth**: `JWTAuthentication` is the default DRF authentication class.
- **Permissions** – `IsAuthenticated` is default; public endpoints must set `AllowAny`.
- **Throttling** – `AnonRateThrottle` (30/min) and `UserRateThrottle` (120/min) are enabled.
- **Testing** – Tests live under each app's `tests.py`; run with `python manage.py test <app>`.
- **Static & Media** – Served via Django's dev server; production uses S3.

## Directory Layout (High-Level)

```
/apps
  /user          – auth, roles, Google OAuth
  /vendors       – vendor profiles, portfolio, ratings
  /design_requests – client job postings, reference images
  /bids          – bidding logic, bid management
  /orders        – order lifecycle, production tracking
  /reviews       – reviews and ratings
  /notifications – in-app notifications
  /messaging     – client-vendor chat
  /disputes      – dispute resolution workflow
  /analytics     – admin analytics endpoints
  /common        – shared utilities (validators)
  /core          – Django core integration (settings, urls, wsgi)
```

This structure enforces clear domain boundaries, promotes reusable services, and keeps views lightweight.