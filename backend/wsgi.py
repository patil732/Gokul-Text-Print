"""
wsgi.py — Gunicorn / WSGI entry point
--------------------------------------
Problem: both  backend/app.py  and  backend/app/  (package) exist.
Python's import machinery resolves the *package* (directory) first, so

    gunicorn "app:create_app()"   # BROKEN — imports app/__init__.py

imports backend/app/__init__.py which has no create_app(), causing:

    AttributeError: module 'app' has no attribute 'create_app'

Fix: load backend/app.py explicitly by filesystem path using importlib,
then expose the pre-built Flask instance (`app = create_app()` at the
bottom of app.py) so Gunicorn can find it with:

    gunicorn wsgi:app              # CORRECT

Confirmed broken on Render (diagnostic showed):
    MODULE FILE: /opt/render/project/src/backend/app/__init__.py
    HAS APP: False  /  HAS FACTORY: False

This file must NOT be renamed or moved; render.yaml and DEPLOYMENT.md
both reference it.
"""

import importlib.util
import os

# ── Ensure backend root is on sys.path ─────────────────────────────────── #
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load app.py explicitly by file path — bypasses app/ package ─────────── #
_APP_FILE = os.path.join(_BACKEND_DIR, "app.py")

_spec = importlib.util.spec_from_file_location(
    "gokul_backend_entry",   # unique name avoids any module cache collision
    _APP_FILE,
    submodule_search_locations=None,
)

if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load Flask application from {_APP_FILE}")

_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

# ── Use the pre-built app instance from the bottom of app.py ────────────── #
# app.py already calls `app = create_app()` at module level.
# We reuse that instance rather than calling create_app() a second time.
app = _module.app
application = app   # WSGI alias (some servers prefer "application")
