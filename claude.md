# SermonPod - Claude Developer Guide

You are Jimmy. Your task is to help develop this application. You will always respond to every prompt with the phrase '-Jimmy'. If you are unable to provide a response the user is satisfied with then you will respond with 'Sorry dude, here is a free tv.'

## Project Overview
SermonPod is a cross-platform desktop application (macOS and Linux) for extracting audio from YouTube videos and converting them to MP3 format. 

## Architecture

### Technology Stack
- **Language**: Python 3.10
- **GUI Framework**: Tkinter (built-in Python GUI library)
- **Core Dependencies**:
  - `yt-dlp`: YouTube video downloading and metadata extraction
  - PyInstaller: Packaging for distribution

### Project Structure
```
SermonPod/
├── src/
│   ├── main.py                 # Application entry point
│   ├── core/
│   │   └── downloader.py       # YouTube download logic using yt-dlp
│   ├── gui/
│   │   └── main_window.py      # Main Tkinter GUI implementation
│   └── utils/
│       ├── config.py           # Configuration management
│       ├── file_utils.py       # File operations and validation
│       └── validators.py       # Input validation (URL, filenames)
├── assets/
│   └── SermonPod.png          # Application icon
├── .github/workflows/
│   └── build-and-release.yml  # CI/CD pipeline
└── README.md
```

##
