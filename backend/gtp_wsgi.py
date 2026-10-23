
import importlib.util
import os

_backend_dir = os.path.dirname(os.path.abspath(__file__))
_app_file = os.path.join(_backend_dir, "app.py")

_spec = importlib.util.spec_from_file_location(
    "gtp_flask_application",
    _app_file,
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

app = _module.app
