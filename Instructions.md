# Instructions.md

This is the living development guide for the Jawak backend. It describes the current state of the system: what modules exist, what each API endpoint does, and how the request flow works for each. It is updated after every completed task or new module — not for bug fixes or minor revisions. When a feature changes, the relevant section below is revised in place rather than appended to.

See [CLAUDE.md](CLAUDE.md) for the architecture conventions this project follows.

## Project bootstrap

Django 6.0 project initialized with `core` as the central project package (settings, root URL conf, WSGI/ASGI). DRF is installed. Database is PostgreSQL hosted on Neon, configured entirely through environment variables in `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) and read in `core/settings.py` via `python-dotenv`. `SECRET_KEY` and `DEBUG` are also environment-driven.

No feature apps exist yet. New modules will be added under `apps/<name>/` per the convention in CLAUDE.md, each with its own models, serializers, views, and urls, mounted in `core/urls.py` under `/api/v1/<name>/`.

No API endpoints exist yet.
