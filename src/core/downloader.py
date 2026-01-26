"""
YouTube downloader module using yt-dlp.
Handles downloading and converting YouTube videos to MP3 format.
"""

import glob
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yt_dlp


class DownloadError(Exception):
    """Custom exception for download-related errors."""

    pass


class YouTubeDownloader:
    """Handles downloading YouTube videos and converting to MP3."""

    def __init__(self, output_dir: str = None, quality: str = "320"):
        """
        Initialize the downloader.

        Args:
            output_dir: Directory where files will be saved. Defaults to Downloads folder.
            quality: Audio quality in kbps (128, 192, or 320). Default is 320.
        """
        self.output_dir = output_dir or str(Path.home() / "Downloads")
        self.quality = quality
        self.progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Set a callback function for progress updates.

        Args:
            callback: Function that receives progress information dict.
        """
        self.progress_callback = callback

    def _progress_hook(self, d: Dict[str, Any]):
        """
        Internal progress hook called by yt-dlp.

        Args:
            d: Progress dictionary from yt-dlp
        """
        if self.progress_callback:
            self.progress_callback(d)

    def _cleanup_extra_files(self, mp3_file: Path):
        """
        Remove extra files left by yt-dlp (webm, m4a, etc.)

        Args:
            mp3_file: Path to the final MP3 file
        """
        output_dir = mp3_file.parent

        # Extensions to remove (common yt-dlp intermediate files)
        extensions_to_remove = [
            "webm",
            "m4a",
            "opus",
            "mp4",
            "part",
            "ytdl",
            "temp",
        ]

        # Remove all files in output directory with these extensions
        for ext in extensions_to_remove:
            pattern = str(output_dir / f"*.{ext}")
            for file_path in glob.glob(pattern):
                try:
                    # Only remove if it's not the mp3 file we just created
                    if file_path != str(mp3_file):
                        os.remove(file_path)
                except Exception:
                    # Silently ignore errors during cleanup
                    pass

    def download(self, url: str, filename: Optional[str] = None) -> str:
        """
        Download a YouTube video and convert to MP3.

        Args:
            url: YouTube video URL
            filename: Optional custom filename (without extension)

        Returns:
            Path to the downloaded MP3 file

        Raises:
            DownloadError: If download fails for any reason
        """
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # Set up output template
        if filename:
            output_template = str(Path(self.output_dir) / f"{filename}.%(ext)s")
        else:
            output_template = str(Path(self.output_dir) / "%(title)s.%(ext)s")

        # Configure yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.quality,
                }
            ],
            "outtmpl": output_template,
            "progress_hooks": [self._progress_hook],
            "quiet": False,
            "no_warnings": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first
                info = ydl.extract_info(url, download=False)
                video_title = info.get("title", "unknown")

                # Download and convert
                ydl.download([url])

                # Construct the output filename
                if filename:
                    output_file = Path(self.output_dir) / f"{filename}.mp3"
                else:
                    # Sanitize the title to match yt-dlp's output
                    output_file = Path(self.output_dir) / f"{video_title}.mp3"

                # Clean up extra files (webm, m4a, etc.) left by yt-dlp
                self._cleanup_extra_files(output_file)

                return str(output_file)

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)

            # Provide user-friendly error messages for common cases
            if "Private video" in error_msg or "members-only" in error_msg:
                raise DownloadError(
                    "This video is private or members-only and cannot be downloaded."
                )
            elif "Video unavailable" in error_msg:
                raise DownloadError(
                    "This video is unavailable. It may have been deleted or made private."
                )
            elif "age" in error_msg.lower() and "restrict" in error_msg.lower():
                raise DownloadError(
                    "This video is age-restricted and cannot be downloaded."
                )
            elif "geo" in error_msg.lower() or "location" in error_msg.lower():
                raise DownloadError(
                    "This video is not available in your location (geo-blocked)."
                )
            else:
                raise DownloadError(f"Download failed: {error_msg}")

        except Exception as e:
            raise DownloadError(f"An unexpected error occurred: {str(e)}")

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get information about a YouTube video without downloading.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary containing video information (title, duration, etc.)

        Raises:
            DownloadError: If fetching info fails
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown"),
                    "view_count": info.get("view_count", 0),
                }
        except Exception as e:
            raise DownloadError(f"Failed to fetch video information: {str(e)}")
