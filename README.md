# YouTube Auto-Upload Automation

Automated YouTube video distribution system that monitors local directories for new video files and automatically uploads them to YouTube with customizable metadata.

## Features

- **Directory Monitoring**: Automatically watches specified directories for new video files
- **Metadata Integration**: Supports JSON-based metadata files for video titles, descriptions, tags, and settings
- **Multiple Formats**: Supports MP4, MOV, AVI, MKV, WMV, and FLV video formats
- **Configurable Settings**: Customizable upload settings, privacy levels, and categories
- **File Management**: Automatically moves processed videos to organized directories
- **Logging**: Comprehensive logging with rotation support
- **Graceful Handling**: Handles interruptions and errors gracefully

## Requirements

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Google Cloud Project with YouTube Data API v3 enabled
- OAuth 2.0 credentials from Google Cloud Console

## Installation

### 1. Install uv (if not already installed)

```powershell
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup Project

```powershell
cd C:\Users\ADMIN\Music\youtube_auto-upload_automation

# Install dependencies using uv
uv sync
```

### 3. Configure Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials JSON file
5. Rename the downloaded file to `client_secrets.json` and place it in the project root

### 4. Configure Application

Copy the example configuration file:

```powershell
Copy-Item config.json.example config.json
```

Edit `config.json` to customize:

- **Watch directories**: Directories to monitor for new videos
- **Upload settings**: Default privacy, category, notifications
- **Metadata settings**: Default titles, descriptions, tags
- **Processing settings**: Where to move uploaded/failed videos

Example configuration sections:

```json
{
  "monitoring": {
    "watch_directories": [
      "C:\\Users\\ADMIN\\Videos\\ToUpload",
      "D:\\RenderOutput"
    ],
    "supported_extensions": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv"]
  },
  "upload_settings": {
    "default_privacy": "private",
    "default_category": "22",
    "notify_subscribers": true
  }
}
```

## Usage

### Run with uv

```powershell
# Run the automation script
uv run youtube-automation
```

Or directly:

```powershell
uv run python -m youtube_auto_upload_automation.main
```

### First Run

On the first run:
1. A browser window will open for Google OAuth authentication
2. Sign in with your YouTube account
3. Grant the requested permissions
4. The credentials will be saved to `token.json` for future use

### Video Metadata

#### Option 1: Use Metadata Files (Recommended)

Create a JSON file alongside your video with the `_metadata.json` suffix:

**Example: `my_video.mp4` → `my_video_metadata.json`**

```json
{
  "title": "My Awesome Video",
  "description": "This is a detailed description of my video.\n\nWith multiple paragraphs!",
  "tags": ["tutorial", "awesome", "youtube"],
  "category_id": "22",
  "privacy_status": "private",
  "made_for_kids": false
}
```

#### Option 2: Use Default Metadata

If no metadata file exists, the system will use defaults from `config.json`:

```json
{
  "metadata": {
    "default_title_template": "{filename}",
    "default_description": "Uploaded automatically",
    "default_tags": ["automated upload"]
  }
}
```

### YouTube Category IDs

Common category IDs:
- `1` - Film & Animation
- `10` - Music
- `20` - Gaming
- `22` - People & Blogs (default)
- `23` - Comedy
- `24` - Entertainment
- `25` - News & Politics
- `26` - Howto & Style
- `27` - Education
- `28` - Science & Technology

[Full list of YouTube categories](https://developers.google.com/youtube/v3/docs/videoCategories/list)

## Directory Structure

```
youtube_auto-upload_automation/
├── youtube_auto_upload_automation/
│   ├── __init__.py
│   ├── main.py                 # Main automation script
│   ├── config.py               # Configuration management
│   ├── file_monitor.py         # Directory monitoring
│   ├── youtube_uploader.py     # YouTube API integration
│   └── metadata_handler.py     # Metadata processing
├── config.json                 # Your configuration (not in git)
├── config.json.example         # Example configuration
├── client_secrets.json         # OAuth credentials (not in git)
├── token.json                  # Saved OAuth token (not in git)
├── pyproject.toml              # Project dependencies
└── README.md                   # This file
```

## Workflow

1. **Monitor**: The system watches configured directories for new video files
2. **Detect**: When a video file is detected and stable (finished copying)
3. **Load Metadata**: Reads metadata from JSON file or uses defaults
4. **Upload**: Uploads video to YouTube with metadata
5. **Move**: Moves processed video to success/failure directory
6. **Track**: Records processed videos to avoid duplicates

## Troubleshooting

### "Configuration file not found"
- Ensure `config.json` exists (copy from `config.json.example`)

### "Client secrets file not found"
- Download OAuth credentials from Google Cloud Console
- Rename to `client_secrets.json` and place in project root

### "Failed to authenticate"
- Check that YouTube Data API v3 is enabled in Google Cloud Console
- Ensure OAuth consent screen is configured
- Delete `token.json` and re-authenticate

### "Quota exceeded"
- YouTube API has daily quota limits
- Check quota usage in Google Cloud Console
- Default quota is 10,000 units/day; uploads cost ~1,600 units each

### Videos not being detected
- Check that watch directories exist and are accessible
- Verify file extensions are in `supported_extensions` list
- Check `min_file_size_mb` setting (files must be larger)
- Review logs in `logs/youtube_automation.log`

## Development

### Install development dependencies

```powershell
uv sync --dev
```

### Run tests

```powershell
uv run pytest
```

## Configuration Options

### Monitoring Settings
- `watch_directories`: List of directories to monitor
- `supported_extensions`: Video file extensions to process
- `check_interval_seconds`: How often to check file stability
- `min_file_size_mb`: Minimum file size to process

### Upload Settings
- `default_privacy`: `public`, `private`, or `unlisted`
- `default_category`: YouTube category ID
- `made_for_kids`: COPPA compliance setting
- `notify_subscribers`: Whether to notify subscribers

### Processing Settings
- `move_after_upload`: Move files after processing
- `processed_directory`: Where to move successful uploads
- `failed_directory`: Where to move failed uploads
- `track_processed_videos`: Prevent duplicate uploads

### Logging Settings
- `log_level`: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `log_file`: Path to log file
- `max_log_size_mb`: Maximum log file size before rotation
- `backup_count`: Number of rotated log files to keep

## Privacy & Security

- **OAuth Tokens**: Keep `client_secrets.json` and `token.json` private
- **Configuration**: `config.json` is gitignored (may contain sensitive paths)
- **API Scopes**: Only requests YouTube upload permission
- **Local Processing**: All processing happens locally

## License

This project is provided as-is for personal use.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `logs/youtube_automation.log`
3. Ensure all configuration files are properly set up
4. Verify YouTube API quota and permissions

## Useful Commands

```powershell
# Run automation
uv run youtube-automation

# Install dependencies
uv sync

# Update dependencies
uv sync --upgrade

# Check Python version
uv run python --version

# View logs
Get-Content logs\youtube_automation.log -Tail 50 -Wait
```

---

**Note**: This automation system requires active monitoring of the quota limits imposed by YouTube Data API. Be mindful of the number of daily uploads to stay within quota limits.
