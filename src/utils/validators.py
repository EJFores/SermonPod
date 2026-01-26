"""
URL validation utilities for SermonPod.
Validates YouTube URLs and extracts video IDs.
"""

import re
from typing import Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def is_valid_youtube_url(url: str) -> bool:
    """
    Check if a URL is a valid YouTube URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid YouTube URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Strip whitespace
    url = url.strip()

    # YouTube URL patterns
    patterns = [
        r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]+",  # youtube.com/watch?v=...
        r"^https?://(www\.)?youtu\.be/[\w-]+",  # youtu.be/...
        r"^https?://(www\.)?youtube\.com/shorts/[\w-]+",  # youtube.com/shorts/...
        r"^https?://(www\.)?youtube\.com/embed/[\w-]+",  # youtube.com/embed/...
    ]

    for pattern in patterns:
        if re.match(pattern, url):
            return True

    return False


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID string, or None if not found
    """
    if not url:
        return None

    url = url.strip()

    # Pattern for youtube.com/watch?v=VIDEO_ID
    match = re.search(r"[?&]v=([^&]+)", url)
    if match:
        return match.group(1)

    # Pattern for youtu.be/VIDEO_ID
    match = re.search(r"youtu\.be/([^?]+)", url)
    if match:
        return match.group(1)

    # Pattern for youtube.com/shorts/VIDEO_ID
    match = re.search(r"/shorts/([^?]+)", url)
    if match:
        return match.group(1)

    # Pattern for youtube.com/embed/VIDEO_ID
    match = re.search(r"/embed/([^?]+)", url)
    if match:
        return match.group(1)

    return None


def validate_and_extract(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a YouTube URL and extract its video ID.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, video_id)
    """
    is_valid = is_valid_youtube_url(url)
    video_id = extract_video_id(url) if is_valid else None
    return is_valid, video_id


def normalize_youtube_url(url: str) -> str:
    """
    Normalize a YouTube URL to standard format.

    Args:
        url: YouTube URL in any supported format

    Returns:
        Normalized URL in youtube.com/watch?v=ID format

    Raises:
        ValidationError: If URL is invalid
    """
    if not is_valid_youtube_url(url):
        raise ValidationError("Invalid YouTube URL")

    video_id = extract_video_id(url)
    if not video_id:
        raise ValidationError("Could not extract video ID from URL")

    return f"https://www.youtube.com/watch?v={video_id}"


def get_validation_message(url: str) -> str:
    """
    Get a user-friendly validation message for a URL.

    Args:
        url: URL to validate

    Returns:
        Human-readable validation message
    """
    if not url or not url.strip():
        return "Please enter a URL"

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        return "URL must start with http:// or https://"

    if "youtube.com" not in url and "youtu.be" not in url:
        return "URL must be from YouTube (youtube.com or youtu.be)"

    if not is_valid_youtube_url(url):
        return "Invalid YouTube URL format"

    video_id = extract_video_id(url)
    if not video_id:
        return "Could not find video ID in URL"

    return "Valid YouTube URL"
