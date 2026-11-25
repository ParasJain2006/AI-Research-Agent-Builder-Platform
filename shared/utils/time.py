"""
shared.utils.time
~~~~~~~~~~~~~~~~~
Timestamp helpers for the CSE AI platform.

All timestamps produced here are in UTC and formatted as ISO 8601 with a
trailing 'Z' suffix (e.g. "2026-10-31T03:45:10Z").
"""

from datetime import datetime, timezone


def utc_now() -> str:
    """Return the current UTC time as an ISO 8601 string.

    Returns
    -------
    str
        Current UTC timestamp in the form ``"YYYY-MM-DDTHH:MM:SSZ"``
        (seconds precision, no microseconds, explicit Z suffix).

    Example
    -------
    >>> ts = utc_now()
    >>> ts.endswith("Z")
    True
    """
    now = datetime.now(tz=timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")
