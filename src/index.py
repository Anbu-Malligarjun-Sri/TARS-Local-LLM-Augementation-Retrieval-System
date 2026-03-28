"""Vercel FastAPI entrypoint.

This module exposes a top-level `app` object in a Vercel-supported location
while reusing the existing API implementation.
"""

from src.interfaces.api import app
