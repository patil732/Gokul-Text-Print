"""
wsgi.py — Gunicorn / WSGI entry point
--------------------------------------
Problem: both  backend/app.py  and  backend/app/  (package) exist.
Python's import machinery resolves the *package* first, so

    gunicorn "app:create_app()"

imports backend/app/__init__.py — which has no create_app() — instead
of backend/app.py.

Fix: load app.py explicitly by filesystem path using importlib, then
expose the Flask application instance as the module-level name `app`
so Gunicorn can find it with:

    gunicorn wsgi:app

This file must NOT be renamed or moved; render.yaml and DEPLOYMENT.md
both reference it.
"""

import importlib.util
import os
import sys

# ── Ensure backend root is on sys.path ─────────────────────────────────── #
_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ── Load app.py by file path (avoids app/ package shadowing) ───────────── #
_spec = importlib.util.spec_from_file_location(
    "app_entry",                              # arbitrary internal module name
    os.path.join(_BACKEND, "app.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# ── Expose the Flask instance Gunicorn needs ───────────────────────────── #
app = _mod.create_app()
application = app          # WSGI alias (some servers expect "application")
