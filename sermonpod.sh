#!/bin/bash

# Check for debug flag
DEBUG=false
DEBUG_LOG="$HOME/Downloads/sermonpod_debug.log"
if [[ "$1" == "--debug" ]]; then
    DEBUG=true
    echo "Debug mode enabled - logs will be saved to $DEBUG_LOG"
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Progress bar function
show_progress() {
    local duration=$1
    local sleep_interval=0.1
    local progress=0
    local bar_length=50

    while [ $progress -le 100 ]; do
        local filled=$((progress * bar_length / 100))
        local empty=$((bar_length - filled))

        printf "\r${BLUE}["
        printf "%${filled}s" | tr ' ' '█'
        printf "%${empty}s" | tr ' ' '░'
        printf "] ${progress}%%${NC}"

        progress=$((progress + 2))
        sleep $sleep_interval
    done
    echo ""
}

# Spinner function for indeterminate progress
show_spinner() {
    local pid=$1
    local spin='-\|/'
    local i=0

    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r${BLUE}[${spin:$i:1}] Loading...${NC}"
        sleep 0.1
    done
    printf "\r"
}

echo -e "${BLUE}=== yt-dlp Installation Checker ===${NC}"
echo ""
echo "Checking for yt-dlp installation..."

# Check if yt-dlp is installed
if command -v yt-dlp &> /dev/null; then
    echo -e "${GREEN}✓ yt-dlp is already installed${NC}"
    echo ""
    yt-dlp --version
    echo ""
    echo "Checking for updates..."

    # Update yt-dlp to latest stable version
    yt-dlp -U 2>&1 | tee /tmp/ytdlp_update.log | grep -E "(Updated|up to date|newest)" || true

    echo -e "${GREEN}✓ yt-dlp is up to date${NC}"
else

echo -e "${YELLOW}✗ yt-dlp is not installed${NC}"
echo -e "${YELLOW}Starting installation...${NC}"
echo ""

# Detect OS and install accordingly
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux installation
    echo -e "${BLUE}Detected: Linux${NC}"

    # Use standalone binary (no Python required)
    echo "Method: Standalone binary (no Python required)"
    echo ""

    # Create local bin directory if it doesn't exist
    mkdir -p "$HOME/.local/bin"

    # Download standalone binary
    (
        curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o "$HOME/.local/bin/yt-dlp" 2>&1
        chmod a+rx "$HOME/.local/bin/yt-dlp"
    ) > /tmp/ytdlp_install.log 2>&1 &
    PID=$!

    show_spinner $PID
    wait $PID
    INSTALL_STATUS=$?

    if [ $INSTALL_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ Installation completed${NC}"
    else
        echo -e "${RED}✗ Installation failed to ~/.local/bin${NC}"
        echo "Trying with sudo to /usr/local/bin..."

        (
            sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp 2>&1
            sudo chmod a+rx /usr/local/bin/yt-dlp
        ) > /tmp/ytdlp_install.log 2>&1 &
        PID=$!

        show_spinner $PID
        wait $PID

        echo -e "${GREEN}✓ Installation completed${NC}"
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS installation
    echo -e "${BLUE}Detected: macOS${NC}"

    if command -v brew &> /dev/null; then
        echo "Method: Homebrew"
        echo ""

        brew install yt-dlp > /tmp/ytdlp_install.log 2>&1 &
        PID=$!

        show_spinner $PID
        wait $PID

        echo -e "${GREEN}✓ Installation completed${NC}"
    else
        echo "Method: pip3"
        echo ""

        pip3 install --user yt-dlp > /tmp/ytdlp_install.log 2>&1 &
        PID=$!

        show_spinner $PID
        wait $PID

        echo -e "${GREEN}✓ Installation completed${NC}"
    fi

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash/Cygwin)
    echo -e "${BLUE}Detected: Windows${NC}"
    echo "Method: pip"
    echo ""

    pip install yt-dlp > /tmp/ytdlp_install.log 2>&1 &
    PID=$!

    show_spinner $PID
    wait $PID

    echo -e "${GREEN}✓ Installation completed${NC}"
fi

# Verify installation
echo ""
echo "Verifying installation..."
sleep 1

# Source bashrc to update PATH if needed
export PATH="$HOME/.local/bin:$PATH"

if command -v yt-dlp &> /dev/null; then
    echo -e "${GREEN}✓ yt-dlp has been successfully installed!${NC}"
    echo ""
    echo "Version information:"
    yt-dlp --version
else
    echo -e "${YELLOW}⚠ Installation completed, but yt-dlp is not in PATH${NC}"
    echo ""
    echo "You may need to restart your terminal or add ~/.local/bin to your PATH"
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo -e "${BLUE}  export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    exit 1
fi
fi

echo ""
echo ""
echo -e "${BLUE}=== MP3 Downloader ===${NC}"
echo ""
echo -e "${YELLOW}Please provide a YouTube URL to download as MP3${NC}"
echo -e "${BLUE}Note: Only YouTube URLs are supported${NC}"
echo ""

# Loop until valid URL is provided
while true; do
    read -p "Enter YouTube URL: " youtube_url

    # Check if empty
    if [[ -z "$youtube_url" ]]; then
        echo -e "${RED}✗ No URL provided. Please try again.${NC}"
        echo ""
        continue
    fi

    # Clean up URL - remove leading/trailing whitespace and quotes
    youtube_url=$(echo "$youtube_url" | xargs | sed -e 's/^["\x27]*//' -e 's/["\x27]*$//')

    # Validate it's a proper YouTube URL format
    if [[ ! "$youtube_url" =~ ^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+.*$ ]] && \
       [[ ! "$youtube_url" =~ ^(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]+.*$ ]]; then
        echo -e "${RED}✗ Invalid YouTube URL format.${NC}"
        echo -e "${YELLOW}Please paste only the YouTube URL (e.g., https://youtube.com/watch?v=...)${NC}"
        echo ""
        continue
    fi

    # Valid URL found
    break
done

echo ""
echo -e "${GREEN}✓ Valid YouTube URL received${NC}"
echo "Downloading: $youtube_url"
echo ""

# Determine Downloads folder
DOWNLOAD_DIR="$HOME/Downloads"

# Create Downloads folder if it doesn't exist
mkdir -p "$DOWNLOAD_DIR"

# Download and convert to MP3
echo "Saving to: $DOWNLOAD_DIR"
echo ""
echo "Starting download..."
echo ""

# Download and convert to MP3 in background
if [ "$DEBUG" = true ]; then
    # Debug mode - save logs to file
    yt-dlp --restrict-filenames -x --audio-format mp3 \
        -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" \
        "$youtube_url" > "$DEBUG_LOG" 2>&1 &
    PID=$!

    show_spinner $PID
    wait $PID
    DOWNLOAD_STATUS=$?

    echo ""

    if [ $DOWNLOAD_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ Download completed successfully!${NC}"
        echo -e "${GREEN}File saved to: $DOWNLOAD_DIR${NC}"
        echo -e "${BLUE}Debug log saved to: $DEBUG_LOG${NC}"
    else
        echo -e "${RED}✗ Download failed${NC}"
        echo -e "${YELLOW}Check debug log at: $DEBUG_LOG${NC}"
        echo ""
        echo "Last 20 lines of log:"
        tail -n 20 "$DEBUG_LOG"
        exit 1
    fi
else
    # Normal mode - hide output
    yt-dlp --restrict-filenames -x --audio-format mp3 \
        -o "$DOWNLOAD_DIR/%(title)s.%(ext)s" \
        "$youtube_url" > /dev/null 2>&1 &
    PID=$!

    show_spinner $PID
    wait $PID
    DOWNLOAD_STATUS=$?

    echo ""

    if [ $DOWNLOAD_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ Download completed successfully!${NC}"
        echo -e "${GREEN}File saved to: $DOWNLOAD_DIR${NC}"
    else
        echo -e "${RED}✗ Download failed${NC}"
        exit 1
    fi
fi
