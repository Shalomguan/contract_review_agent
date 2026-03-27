"""Pytest configuration for local imports and test client compatibility."""
from pathlib import Path
import sys
import inspect

import httpx


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Starlette's TestClient in the FastAPI version used by this project still passes
# `app=` into httpx.Client. httpx 0.28 removed that keyword. Ignore it in tests so
# local environments with newer httpx can still run the suite.
if "app" not in inspect.signature(httpx.Client.__init__).parameters:
    _original_client_init = httpx.Client.__init__

    def _patched_client_init(self, *args, app=None, **kwargs):
        return _original_client_init(self, *args, **kwargs)

    httpx.Client.__init__ = _patched_client_init
