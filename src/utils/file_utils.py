"""
File management utilities for SermonPod.
Handles file path operations, validation, and sanitization.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional


class FileUtilsError(Exception):
    """Custom exception for file utility errors."""

    pass


def get_default_output_dir() -> str:
    """
    Get the default output directory (user's Downloads folder).

    Returns:
        Path to the Downloads folder as a string
    """
    downloads_dir = Path.home() / "Downloads"
    return str(downloads_dir)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for the filesystem
    """
    # Remove or replace invalid characters for cross-platform compatibility
    # Invalid chars: < > : " / \ | ? *
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, "_", filename)

    # Remove leading/trailing spaces and periods
    sanitized = sanitized.strip(". ")

    # Ensure filename is not empty
    if not sanitized:
        sanitized = "untitled"

    # Limit filename length (255 chars is common limit, leave room for extension)
    max_length = 240
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_output_path(output_dir: str) -> bool:
    """
    Validate that an output directory path is valid and writable.

    Args:
        output_dir: Directory path to validate

    Returns:
        True if valid and writable, False otherwise

    Raises:
        FileUtilsError: If path is invalid or not writable
    """
    path = Path(output_dir)

    # Check if path exists
    if not path.exists():
        # Try to create it
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise FileUtilsError(
                f"Permission denied: Cannot create directory '{output_dir}'"
            )
        except Exception as e:
            raise FileUtilsError(f"Cannot create directory '{output_dir}': {str(e)}")

    # Check if it's a directory
    if not path.is_dir():
        raise FileUtilsError(f"Path '{output_dir}' exists but is not a directory")

    # Check if writable
    if not os.access(path, os.W_OK):
        raise FileUtilsError(f"Directory '{output_dir}' is not writable")

    return True


def get_available_space(path: str) -> int:
    """
    Get available disk space at the given path in bytes.

    Args:
        path: Directory path to check

    Returns:
        Available space in bytes
    """
    stat = shutil.disk_usage(path)
    return stat.free


def check_sufficient_space(path: str, required_bytes: int = 100 * 1024 * 1024) -> bool:
    """
    Check if there's sufficient disk space available.

    Args:
        path: Directory path to check
        required_bytes: Minimum required space in bytes (default: 100MB)

    Returns:
        True if sufficient space available, False otherwise

    Raises:
        FileUtilsError: If insufficient disk space
    """
    available = get_available_space(path)

    if available < required_bytes:
        available_mb = available / (1024 * 1024)
        required_mb = required_bytes / (1024 * 1024)
        raise FileUtilsError(
            f"Insufficient disk space. Available: {available_mb:.2f}MB, "
            f"Required: {required_mb:.2f}MB"
        )

    return True


def resolve_file_conflict(filepath: str, overwrite: bool = False) -> str:
    """
    Resolve filename conflicts by adding a number suffix if needed.

    Args:
        filepath: Original file path
        overwrite: If True, return original path (will overwrite)

    Returns:
        Non-conflicting file path
    """
    path = Path(filepath)

    # If file doesn't exist or overwrite is True, return as-is
    if not path.exists() or overwrite:
        return filepath

    # Add number suffix to avoid conflicts
    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return str(new_path)
        counter += 1


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def open_file_location(filepath: str) -> bool:
    """
    Open the file's directory in the system file manager.

    Args:
        filepath: Path to the file

    Returns:
        True if successful, False otherwise
    """
    import platform
    import subprocess

    path = Path(filepath)
    directory = path.parent if path.is_file() else path

    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            subprocess.run(["open", str(directory)], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", str(directory)], check=True)
        else:
            # Unsupported platform
            return False

        return True

    except Exception:
        return False
