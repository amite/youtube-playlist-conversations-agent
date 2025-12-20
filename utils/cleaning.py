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


# ============================================================================
# PHASE 0.2: SEMANTIC CLEANING FUNCTIONS
# ============================================================================


def remove_urls(text: str) -> str:
    """Remove URLs from text.

    Removes: http(s), www, bit.ly, and other URL patterns.

    Args:
        text: Text potentially containing URLs

    Returns:
        Text with URLs removed
    """
    # Match: https://, http://, www., bit.ly/, etc.
    pattern = r'https?://\S+|www\.\S+|bit\.ly/\S+'
    cleaned = re.sub(pattern, '', text)
    return cleaned


def remove_timestamps(text: str) -> str:
    """Remove timestamp patterns from text.

    Removes: HH:MM:SS, MM:SS, [MM:SS], and timestamp lines.

    Args:
        text: Text potentially containing timestamps

    Returns:
        Text with timestamps removed
    """
    # Remove various timestamp formats
    # HH:MM:SS or MM:SS:SS
    text = re.sub(r'\d{1,2}:\d{2}:\d{2}', '', text)
    # MM:SS or H:MM
    text = re.sub(r'\d{1,2}:\d{2}(?=\s|$|[^\d])', '', text)
    # [MM:SS] or [HH:MM:SS]
    text = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]', '', text)
    return text


def remove_social_ctas(text: str) -> str:
    """Remove call-to-action sentences from text.

    Removes sentences containing: subscribe, follow, newsletter, check out, click here.

    Args:
        text: Text potentially containing CTAs

    Returns:
        Text with CTA sentences removed
    """
    # CTA keywords to detect
    cta_keywords = [
        r'subscribe',
        r'follow\s+me',
        r'newsletter',
        r'check\s+out',
        r'click\s+here',
    ]

    # Remove sentences containing CTA keywords (case-insensitive)
    for keyword in cta_keywords:
        # Match sentence (ending with . ! ? or newline) containing the keyword
        pattern = rf'[^.!?\n]*\b{keyword}\b[^.!?\n]*[.!?\n]'
        text = re.sub(pattern, '\n', text, flags=re.IGNORECASE)

    return text


def remove_boilerplate_sections(text: str) -> str:
    """Remove boilerplate sections from text.

    Removes sections starting with: Resources, Links, Chapters, Timestamps, etc.

    Args:
        text: Text potentially containing boilerplate

    Returns:
        Text with boilerplate sections removed
    """
    # Boilerplate section headers
    boilerplate_headers = [
        r'Resources:',
        r'Links:',
        r'Chapters:',
        r'Timestamps:',
        r'Affiliate\s+disclosure:',
        r'Sponsored\s+by',
        r'This\s+video\s+is\s+brought\s+to\s+you',
    ]

    # Remove everything from these headers to the end
    for header in boilerplate_headers:
        # Remove from header to end of text
        text = re.sub(rf'\n?{header}.*$', '', text, flags=re.IGNORECASE | re.DOTALL)

    return text


def extract_core_content(text: str, max_paragraphs: int = 3) -> str:
    """Extract core content from text (first N paragraphs).

    Keeps substantive content, removes boilerplate.

    Args:
        text: Text to extract content from
        max_paragraphs: Maximum number of paragraphs to keep

    Returns:
        Text with only core content
    """
    # If text is short, keep all of it
    if len(text) < 200:
        return text

    # Split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')

    # Filter out very short or boilerplate-like paragraphs
    content_paragraphs = []
    for para in paragraphs[:max_paragraphs]:
        if len(para.strip()) > 20:
            content_paragraphs.append(para)

    return '\n\n'.join(content_paragraphs) if content_paragraphs else text


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Collapses multiple newlines/spaces to single.

    Args:
        text: Text with potential whitespace issues

    Returns:
        Text with normalized whitespace
    """
    # Collapse multiple newlines to single
    text = re.sub(r'\n{2,}', '\n', text)
    # Collapse multiple spaces to single
    text = re.sub(r' {2,}', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def clean_description_semantic(text: str) -> str:
    """Apply semantic cleaning to description.

    Removes URLs, timestamps, CTAs, and boilerplate.
    Extracts core content and normalizes whitespace.

    Args:
        text: Raw description text

    Returns:
        Semantically cleaned description
    """
    if not text or not text.strip():
        return "[No Description]"

    # Apply cleaning functions in order
    cleaned = text
    cleaned = remove_urls(cleaned)
    cleaned = remove_timestamps(cleaned)
    cleaned = remove_boilerplate_sections(cleaned)
    cleaned = remove_social_ctas(cleaned)
    cleaned = extract_core_content(cleaned, max_paragraphs=3)
    cleaned = normalize_whitespace(cleaned)

    # If over-cleaning occurred, fallback to just URL removal
    if len(cleaned) < 50 and len(text) > 100:
        cleaned = text
        cleaned = remove_urls(cleaned)
        cleaned = normalize_whitespace(cleaned)

    return cleaned


def remove_emojis(title: str) -> str:
    """Remove emoji characters from title.

    Args:
        title: Title potentially containing emojis

    Returns:
        Title with emojis removed
    """
    # Remove emojis using Unicode ranges
    # This covers most common emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r'', title)


def remove_excessive_punctuation(title: str) -> str:
    """Remove excessive punctuation from title.

    Replaces !!!, ???, ... with single punctuation marks.

    Args:
        title: Title with potential excessive punctuation

    Returns:
        Title with excessive punctuation reduced
    """
    # Replace multiple ! with single !
    title = re.sub(r'!{2,}', '!', title)
    # Replace multiple ? with single ?
    title = re.sub(r'\?{2,}', '?', title)
    # Replace multiple . with single . (but not in ellipsis context)
    title = re.sub(r'\.{3,}', '.', title)
    return title


def normalize_caps(title: str) -> str:
    """Normalize excessive capitalization in title.

    Converts all-caps words to Title Case, except known acronyms.

    Args:
        title: Title with potential excessive caps

    Returns:
        Title with normalized capitalization
    """
    # Known acronyms to preserve
    acronyms = {
        'AI', 'API', 'LLM', 'GPU', 'CPU', 'RAM', 'SSD',
        'AWS', 'GCP', 'SQL', 'HTTP', 'HTTPS', 'URL', 'CSV',
        'JSON', 'XML', 'REST', 'CRUD', 'MVVM', 'MVC',
        'UI', 'UX', 'DX', 'CI', 'CD', 'DevOps',
        'ML', 'NLP', 'CV', 'RNN', 'CNN', 'GAN',
        'IoT', 'API', 'SDK', 'IDE', 'CLI', 'GUI',
    }

    # Process word by word
    words = title.split()
    result = []

    for word in words:
        # Check if word (without punctuation) is all caps and >3 chars
        word_stripped = word.rstrip('.,!?;:')
        if word_stripped.isupper() and len(word_stripped) > 2:
            # If it's a known acronym, keep it
            if word_stripped in acronyms:
                result.append(word)
            else:
                # Convert to Title Case (capitalize first letter only)
                result.append(word_stripped.capitalize() + word[len(word_stripped):])
        else:
            result.append(word)

    return ' '.join(result)


def remove_clickbait_patterns(title: str) -> str:
    """Remove clickbait patterns from title.

    Removes: SHOCKING, You WON'T BELIEVE, Just Changed EVERYTHING, etc.

    Args:
        title: Title with potential clickbait

    Returns:
        Title with clickbait removed
    """
    clickbait_patterns = [
        r"SHOCKING",
        r"You\s+WON'?T\s+BELIEVE",
        r"Just\s+Changed\s+EVERYTHING",
        r"BLEW\s+MY\s+MIND",
        r"INSANE",
        r"CRAZY",
    ]

    for pattern in clickbait_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    return title


def clean_title_semantic(title: str) -> str:
    """Apply semantic cleaning to title.

    Removes emojis, excessive punctuation, normalizes caps, removes clickbait.

    Args:
        title: Raw title text

    Returns:
        Semantically cleaned title
    """
    if not title:
        return ""

    # Apply cleaning functions in order
    cleaned = title
    cleaned = remove_emojis(cleaned)
    cleaned = remove_excessive_punctuation(cleaned)
    cleaned = normalize_caps(cleaned)
    cleaned = remove_clickbait_patterns(cleaned)
    cleaned = cleaned.strip()

    return cleaned
