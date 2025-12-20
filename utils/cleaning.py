"""Data cleaning utilities for YouTube video metadata."""

import re
from datetime import datetime
from typing import Optional


def parse_iso_duration(duration_str: Optional[str]) -> Optional[int]:
    """Parse ISO 8601 duration string (e.g., 'PT1H46M33S') to seconds.

    Args:
        duration_str: ISO 8601 duration string or None

    Returns:
        Duration in seconds, or None if parsing fails
    """
    if not duration_str:
        return None

    # ISO 8601 pattern: PT[hours]H[minutes]M[seconds]S
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration_str)

    if not match:
        return None

    hours, minutes, seconds = match.groups()
    total_seconds = 0

    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)

    return total_seconds


def parse_iso_datetime(datetime_str: Optional[str]) -> Optional[int]:
    """Parse ISO 8601 datetime string to Unix timestamp.

    Args:
        datetime_str: ISO 8601 datetime string (e.g., '2025-09-25T11:00:31Z')

    Returns:
        Unix timestamp (seconds since epoch), or None if parsing fails
    """
    if not datetime_str:
        return None

    try:
        # Handle timezone-aware datetime
        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except (ValueError, AttributeError):
        return None


def parse_integer(value: Optional[str]) -> Optional[int]:
    """Parse string to integer, handling None and invalid values.

    Args:
        value: String representation of integer or None

    Returns:
        Integer value or None if parsing fails
    """
    if not value:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def clean_description(description: Optional[str]) -> str:
    """Clean description text (basic Phase 0.1 version).

    In Phase 0.1, we just fill missing descriptions.
    Semantic cleaning patterns are Phase 0.2.

    Args:
        description: Raw description text or None

    Returns:
        Cleaned description or placeholder if None
    """
    if not description or not description.strip():
        return "[No Description]"
    return description


def clean_title(title: Optional[str]) -> str:
    """Clean title text (basic Phase 0.1 version).

    In Phase 0.1, just ensure it exists.
    Advanced cleaning is Phase 0.2.

    Args:
        title: Raw title text or None

    Returns:
        Title or empty string if None
    """
    if not title:
        return ""
    return title.strip()
