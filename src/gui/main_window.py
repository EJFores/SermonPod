"""
Main GUI window for SermonPod.
Provides interface for downloading YouTube videos as MP3 files.
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from ..core.downloader import DownloadError, YouTubeDownloader
from ..utils.config import ConfigManager
from ..utils.file_utils import (
    FileUtilsError,
    open_file_location,
    sanitize_filename,
    validate_output_path,
)
from ..utils.validators import get_validation_message, is_valid_youtube_url


class SermonPodGUI:
    """Main application window for SermonPod."""

    def __init__(self, root: tk.Tk):
        """
        Initialize the GUI.

        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("SermonPod")
        self.root.resizable(False, False)

        # Set application icon
        self._set_icon()

        # Initialize configuration manager
        self.config_manager = ConfigManager()

        # Application state
        self.output_dir = self.config_manager.get_output_directory()
        self.downloading = False
        self.download_thread: Optional[threading.Thread] = None
        self.progress_queue = queue.Queue()
        self.downloaded_file: Optional[str] = None

        # Create downloader instance
        self.downloader = YouTubeDownloader(output_dir=self.output_dir)
        self.downloader.set_progress_callback(self._on_progress)

        # Build the UI
        self._build_ui()

        # Center window on screen after UI is built
        self._center_window()

        # Start checking progress queue
        self._check_progress_queue()

    def _set_icon(self):
        """Set the application icon."""
        try:
            # Get the icon path relative to the project root
            icon_path = Path(__file__).parent.parent.parent / "assets" / "SermonPod.png"
            if icon_path.exists():
                # For Linux and Windows
                icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, icon)
                # Keep a reference to prevent garbage collection
                self._icon = icon
        except Exception:
            # Silently fail if icon cannot be loaded
            pass

    def _center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        window_width = 600
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _build_ui(self):
        """Build the user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # --- Input Section ---
        input_frame = ttk.LabelFrame(main_frame, text="YouTube URL", padding="10")
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # URL entry with validation
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=0, sticky="ew")
        self.url_entry.bind("<KeyRelease>", self._on_url_change)
        self.url_entry.bind("<Control-v>", self._on_paste)
        self.url_entry.bind("<Command-v>", self._on_paste)

        # Validation indicator
        self.validation_label = ttk.Label(input_frame, text="", foreground="gray")
        self.validation_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # --- Output Section ---
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Output directory
        ttk.Label(output_frame, text="Output Directory:").grid(
            row=0, column=0, sticky=tk.W
        )

        dir_container = ttk.Frame(output_frame)
        dir_container.grid(row=1, column=0, sticky="ew", pady=(5, 10))

        self.dir_entry = ttk.Entry(dir_container, width=50)
        self.dir_entry.insert(0, self.output_dir)
        self.dir_entry.config(state="readonly")
        self.dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        browse_btn = ttk.Button(
            dir_container, text="Browse", command=self._browse_directory
        )
        browse_btn.grid(row=0, column=1)

        dir_container.columnconfigure(0, weight=1)

        # Filename
        ttk.Label(output_frame, text="Filename:").grid(row=2, column=0, sticky=tk.W)

        self.filename_entry = ttk.Entry(output_frame, width=50)
        self.filename_entry.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        self.filename_entry.bind("<KeyRelease>", self._on_filename_change)

        # --- Action Section ---
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        self.download_btn = ttk.Button(
            action_frame,
            text="Download and Convert",
            command=self._start_download,
            width=20,
            state="disabled",
        )
        self.download_btn.grid(row=0, column=0, pady=(0, 10))

        # Download progress bar
        ttk.Label(action_frame, text="Download Progress:", anchor=tk.W).grid(
            row=1, column=0, sticky=tk.W, pady=(0, 2)
        )
        self.download_progress_var = tk.DoubleVar()
        self.download_progress_bar = ttk.Progressbar(
            action_frame,
            variable=self.download_progress_var,
            maximum=100,
            mode="determinate",
            length=560,
        )
        self.download_progress_bar.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Conversion progress bar
        ttk.Label(action_frame, text="Conversion Progress:", anchor=tk.W).grid(
            row=3, column=0, sticky=tk.W, pady=(0, 2)
        )
        self.conversion_progress_var = tk.DoubleVar()
        self.conversion_progress_bar = ttk.Progressbar(
            action_frame,
            variable=self.conversion_progress_var,
            maximum=100,
            mode="determinate",
            length=560,
        )
        self.conversion_progress_bar.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # Status label
        self.status_label = ttk.Label(
            action_frame, text="Ready", foreground="gray", anchor=tk.W
        )
        self.status_label.grid(row=5, column=0, sticky="ew")

        action_frame.columnconfigure(0, weight=1)

        # --- Post-Download Section ---
        post_download_frame = ttk.Frame(main_frame)
        post_download_frame.grid(row=3, column=0, sticky="ew")

        self.open_folder_btn = ttk.Button(
            post_download_frame,
            text="Open Output Folder",
            command=self._open_output_folder,
            state="disabled",
        )
        self.open_folder_btn.grid(row=0, column=0)

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)

    def _on_url_change(self, event=None):
        """Handle URL entry changes for validation."""
        url = self.url_entry.get().strip()

        if not url:
            self.validation_label.config(text="", foreground="gray")
            self.filename_entry.delete(0, tk.END)
            return

        # Validate URL
        if is_valid_youtube_url(url):
            self.validation_label.config(text="✓ Valid YouTube URL", foreground="green")
            # Try to fetch video info and auto-populate filename
            self._fetch_video_info(url)
        else:
            message = get_validation_message(url)
            self.validation_label.config(text=f"✗ {message}", foreground="red")
            self.filename_entry.delete(0, tk.END)

    def _fetch_video_info(self, url: str):
        """Fetch video info in background and populate filename."""

        def fetch():
            try:
                info = self.downloader.get_video_info(url)
                title = sanitize_filename(info["title"])
                self.root.after(0, lambda: self._set_filename(title))
            except Exception:
                # Silently fail - not critical
                pass

        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()

    def _set_filename(self, filename: str):
        """Set the filename entry (called from main thread)."""
        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, filename)
        # Check if file exists after setting filename
        self._on_filename_change()

    def _on_filename_change(self, event=None):
        """Check if the output file already exists."""
        filename = self.filename_entry.get().strip()

        if not filename:
            # Disable button if filename is empty
            if not self.downloading:
                self.status_label.config(text="Ready", foreground="gray")
                self.download_btn.config(state="disabled")
            return

        # Sanitize and add .mp3 extension
        sanitized = sanitize_filename(filename)
        if not sanitized.endswith(".mp3"):
            sanitized += ".mp3"

        # Check if file exists in output directory
        output_path = Path(self.output_dir) / sanitized

        if output_path.exists():
            self.status_label.config(
                text=f"Error: '{sanitized}' already exists in output folder",
                foreground="red",
            )
            # Disable download button
            self.download_btn.config(state="disabled")
        else:
            # Only update status if not downloading
            if not self.downloading:
                self.status_label.config(text="Ready", foreground="gray")
                self.download_btn.config(state="normal")

    def _on_paste(self, event=None):
        """Handle paste keyboard shortcut."""
        self.root.after(100, self._on_url_change)

    def _browse_directory(self):
        """Open directory browser dialog."""
        directory = filedialog.askdirectory(
            title="Select Output Directory", initialdir=self.output_dir
        )

        if directory:
            self.output_dir = directory
            self.dir_entry.config(state="normal")
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.dir_entry.config(state="readonly")
            self.downloader.output_dir = directory
            # Save the output directory preference
            self.config_manager.set_output_directory(directory)

    def _start_download(self):
        """Start the download process."""
        # Validate URL
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        if not is_valid_youtube_url(url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return

        # Validate output directory
        try:
            validate_output_path(self.output_dir)
        except FileUtilsError as e:
            messagebox.showerror("Error", str(e))
            return

        # Get filename
        filename = self.filename_entry.get().strip()
        if filename:
            filename = sanitize_filename(filename)

        # Disable controls
        self._set_downloading_state(True)

        # Reset progress
        self.download_progress_var.set(0)
        self.conversion_progress_var.set(0)
        self.status_label.config(text="Starting download...", foreground="blue")
        self.downloaded_file = None

        # Start download in background thread
        self.download_thread = threading.Thread(
            target=self._download_worker, args=(url, filename), daemon=True
        )
        self.download_thread.start()

    def _download_worker(self, url: str, filename: Optional[str]):
        """Worker function for download thread."""
        try:
            output_file = self.downloader.download(url, filename)
            self.progress_queue.put({"status": "complete", "file": output_file})
        except DownloadError as e:
            self.progress_queue.put({"status": "error", "message": str(e)})
        except Exception as e:
            self.progress_queue.put(
                {"status": "error", "message": f"Unexpected error: {str(e)}"}
            )

    def _on_progress(self, d: dict):
        """Callback for download progress updates."""
        self.progress_queue.put({"status": "progress", "data": d})

    def _check_progress_queue(self):
        """Check for progress updates from download thread."""
        try:
            while True:
                msg = self.progress_queue.get_nowait()

                if msg["status"] == "progress":
                    self._handle_progress_update(msg["data"])
                elif msg["status"] == "complete":
                    self._handle_download_complete(msg["file"])
                elif msg["status"] == "error":
                    self._handle_download_error(msg["message"])

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self._check_progress_queue)

    def _handle_progress_update(self, data: dict):
        """Handle progress update from yt-dlp."""
        status = data.get("status")

        if status == "downloading":
            # Calculate percentage
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)

            if total > 0:
                percent = (downloaded / total) * 100
                self.download_progress_var.set(percent)
                self.status_label.config(
                    text=f"Downloading: {percent:.1f}%", foreground="blue"
                )

        elif status == "finished":
            self.download_progress_var.set(100)
            self.status_label.config(text="Converting to MP3...", foreground="blue")
            # Start conversion progress animation
            self._animate_conversion_progress()

        elif status == "processing":
            # Handle post-processing updates if available
            self.conversion_progress_var.set(50)
            self.status_label.config(text="Processing audio...", foreground="blue")

    def _animate_conversion_progress(self):
        """Animate the conversion progress bar since yt-dlp doesn't provide conversion progress."""
        current = self.conversion_progress_var.get()
        if current < 100 and self.downloading:
            # Increment progress smoothly
            self.conversion_progress_var.set(min(current + 2, 95))
            self.root.after(100, self._animate_conversion_progress)

    def _handle_download_complete(self, output_file: str):
        """Handle successful download completion."""
        self.downloaded_file = output_file
        self.download_progress_var.set(100)
        self.conversion_progress_var.set(100)
        self.status_label.config(
            text=f"Success: {Path(output_file).name}", foreground="green"
        )
        self._set_downloading_state(False)
        self.open_folder_btn.config(state="normal")
        # Save the last used filename
        self.config_manager.set_last_filename(Path(output_file).stem)

    def _handle_download_error(self, message: str):
        """Handle download error."""
        self.status_label.config(text=f"Error: {message}", foreground="red")
        self.download_progress_var.set(0)
        self.conversion_progress_var.set(0)
        self._set_downloading_state(False)

    def _set_downloading_state(self, downloading: bool):
        """Enable/disable controls based on download state."""
        self.downloading = downloading

        state = "disabled" if downloading else "normal"
        self.url_entry.config(state=state)
        self.download_btn.config(state=state)

        if downloading:
            self.download_btn.config(text="Downloading...")
        else:
            self.download_btn.config(text="Download and Convert")

    def _open_output_folder(self):
        """Open the output folder in file manager."""
        if self.downloaded_file:
            success = open_file_location(self.downloaded_file)
            if not success:
                messagebox.showinfo(
                    "Output Folder", f"File saved to:\n{self.downloaded_file}"
                )
        else:
            success = open_file_location(self.output_dir)
            if not success:
                messagebox.showinfo(
                    "Output Folder", f"Output directory:\n{self.output_dir}"
                )


def create_main_window() -> tk.Tk:
    """
    Create and configure the main application window.

    Returns:
        Configured Tkinter root window
    """
    root = tk.Tk()
    return root
