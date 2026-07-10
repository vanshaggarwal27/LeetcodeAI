"""Minimal shim for imghdr to satisfy imports during tests.

This provides a no-op `what` implementation sufficient for tests
that don't rely on image type detection.
"""
from typing import Optional


def what(file, h: Optional[bytes] = None) -> Optional[str]:
    return None
