# Cojum Dip Lost Media Scraper (DERP)

**D**iscovering **E**lusive **R**ecordings **P**roject

A comprehensive archival tool for the Cojumpendium research group to find lost media from the band Cojum Dip (2004-2011).

## About

This powerful scraping tool helps locate archived photos, videos, audio, and mentions of Cojum Dip across old social media and music platforms. It searches archived versions of MySpace, Soundcloud, Facebook, Twitter, YouTube, Last.fm, Flickr, PureVolume, and various forums through the Wayback Machine.

### Background

Cojum Dip is an experimental band founded by Bora Karaca around 2004 at the University of Michigan. The band has significant lost media from the pre-2011 era. The Cojumpendium research group has the founder's full support for this archival effort, which will help with the current album rollout.

**Priority target**: Finding "Turk Off" / "2010 Remix" release

## Features

### Core Capabilities
- **Wayback Machine Integration** - Comprehensive archive searches using CDX Server API
- **Multi-Platform Scraping** - Support for MySpace, Soundcloud, Facebook, Twitter, YouTube, Last.fm, Flickr, and more
- **Media Extraction** - Automatic detection and download of images, videos, and audio files
- **Smart Deduplication** - File hashing to avoid duplicate downloads
- **SQLite Database** - Track all discovered URLs and their status
- **Export Options** - JSON, CSV, and HTML report generation
- **Async Operations** - Fast, concurrent HTTP requests with rate limiting
- **Progress Tracking** - Rich terminal UI with progress bars and status updates

### Search Targets
The scraper searches for:
- Band names: "Cojum Dip", "cojumdip", "cojum-dip"
- Key members: "Bora Karaca"
- **HIGH PRIORITY**: "Turk Off", "2010 Remix"
- Band personas: "Bodur the Clumsy", "Udabn the Feared", "Captain No the Love Machine", "Mumutits the Sour", "Oktabis the Keeper"
- Venue combinations: "Blind Pig Cojum", "Duderstadt Center Cojum"
- Related searches: "Tally Hall Bora", "Ann Arbor experimental metal"
- Album/EP names: "Anthropomorphic Bible Assault", "Greatest Demo CD in the Universe"

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/cajumdip/derp.git
cd derp
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize the scraper**
```bash
python -m cojumpendium_scraper init
```

This will:
- Create `config.yaml` from the example template
- Initialize the SQLite database
- Create required directories (downloads, exports)

## Configuration

Edit `config.yaml` to customize the scraper behavior:

```yaml
# General settings
general:
  download_dir: "./downloads"
  database: "./cojumpendium.db"
  log_level: "INFO"

# HTTP settings
http:
  max_concurrent: 10
  request_delay: 1.0
  timeout: 30

# Search settings
search:
  terms:
    - "Cojum Dip"
    - "Bora Karaca"
    - "Turk Off"
    - "2010 Remix"
  date_range:
    start: "2004-01-01"
    end: "2011-12-31"

# Platform-specific settings
platforms:
  myspace:
    enabled: true
  soundcloud:
    enabled: true
  # ... more platforms
```

See `config.example.yaml` for all available options.

## Usage

### Basic Scraping

Run the scraper to search all enabled platforms:

```bash
python -m cojumpendium_scraper scrape
```

### Platform-Specific Scraping

Scrape specific platforms only:

```bash
python -m cojumpendium_scraper scrape --platform wayback --platform myspace
```

### Dry Run Mode

Test without saving to database:

```bash
python -m cojumpendium_scraper scrape --dry-run
```

### View Statistics

Check scraping progress and statistics:

```bash
python -m cojumpendium_scraper stats
```

### Export Data

Export discovered content:

```bash
# Export all formats
python -m cojumpendium_scraper export

# Export specific format
python -m cojumpendium_scraper export --format json
python -m cojumpendium_scraper export --format csv
python -m cojumpendium_scraper export --format html
```

### Verbose Mode

Enable detailed logging:

```bash
python -m cojumpendium_scraper --verbose scrape
```

### Custom Configuration

Use a custom config file:

```bash
python -m cojumpendium_scraper --config /path/to/config.yaml scrape
```

## Project Structure

```
cojumpendium_scraper/
├── __init__.py           # Package initialization
├── __main__.py           # CLI entry point
├── cli.py                # Command-line interface
├── config.py             # Configuration management
├── database.py           # SQLite database operations
├── scrapers/             # Platform-specific scrapers
│   ├── base.py           # Base scraper class
│   ├── wayback.py        # Wayback Machine scraper
│   ├── myspace.py        # MySpace scraper
│   ├── soundcloud.py     # Soundcloud scraper
│   ├── facebook.py       # Facebook scraper
│   ├── twitter.py        # Twitter scraper
│   ├── youtube.py        # YouTube scraper
│   ├── lastfm.py         # Last.fm scraper
│   ├── flickr.py         # Flickr scraper
│   └── forums.py         # Forums scraper
├── extractors/           # Media extraction
│   ├── media.py          # Base media extractor
│   ├── images.py         # Image extractor
│   ├── video.py          # Video extractor
│   └── audio.py          # Audio extractor
├── utils/                # Utility modules
│   ├── http.py           # HTTP client with rate limiting
│   ├── hashing.py        # File hashing for deduplication
│   └── logging.py        # Logging configuration
└── exporters/            # Data export
    ├── json_export.py    # JSON exporter
    ├── csv_export.py     # CSV exporter
    └── html_report.py    # HTML report generator
```

## Database Schema

### URLs Table
Tracks all discovered URLs:
- `id` - Primary key
- `url` - The URL
- `source_platform` - Platform where found
- `archive_date` - Archive date if applicable
- `content_type` - Type of content
- `status` - Processing status (pending/processing/completed/error)
- `discovered_at` - When discovered
- `last_checked` - Last check timestamp
- `metadata` - Additional metadata (JSON)

### Media Files Table
Tracks downloaded media:
- `id` - Primary key
- `url_id` - Foreign key to URLs
- `file_path` - Local file path
- `file_type` - Type (image/video/audio)
- `file_hash` - Hash for deduplication
- `file_size` - Size in bytes
- `original_url` - Original URL
- `downloaded_at` - Download timestamp
- `reviewed` - Review status
- `notes` - Review notes

## Platform-Specific Notes

### Wayback Machine
- Uses CDX Server API for efficient archive searches
- Respects rate limits (default: 30 requests/minute)
- Searches archived snapshots from 2004-2011

### MySpace
- Focuses on archived profile pages
- Extracts old music player links
- Looks for photos and comments

### Soundcloud
- Searches for tracks and reposts
- Extracts embedded audio players

### YouTube
- Extracts video IDs from search results
- Can be used with yt-dlp for downloads

### Last.fm
- Searches artist pages for scrobbles
- Looks for photos and event listings

### Flickr
- Searches by tags and venue names
- Extracts photo URLs

## Tips for Effective Scraping

1. **Start with Wayback Machine** - This is the primary source for archived content
2. **Use specific search terms** - The more specific, the better results
3. **Monitor rate limits** - Adjust `request_delay` in config if needed
4. **Review statistics regularly** - Use `stats` command to track progress
5. **Export periodically** - Save your progress with `export` command
6. **Check logs** - Review `scraper.log` for detailed information

## Contributing

This is a community effort! Cojumpendium members can contribute by:

1. **Adding search terms** - Edit `config.yaml` to add more search terms
2. **Improving scrapers** - Enhance platform-specific scrapers
3. **Adding platforms** - Create new scrapers for additional platforms
4. **Reporting findings** - Share discovered media with the group
5. **Testing** - Run scrapes and report issues

## Troubleshooting

### Common Issues

**"Database not found"**
- Run `python -m cojumpendium_scraper init` to initialize

**"Rate limit exceeded"**
- Increase `request_delay` in config.yaml
- Reduce `max_concurrent` in config.yaml

**"Failed to download media"**
- Check internet connection
- Some archived URLs may be unavailable
- Check logs for specific errors

**"Import errors"**
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## Legal and Ethical Considerations

- This tool respects robots.txt and rate limits
- Archives content for historical preservation purposes
- Has explicit permission from the band founder (Bora Karaca)
- Complies with Archive.org's terms of service

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Bora Karaca and Cojum Dip for supporting this archival effort
- The Cojumpendium research group
- Archive.org for preserving internet history

## Contact

For questions or to contribute, please open an issue on GitHub.

---

**Remember**: The goal is to preserve lost media for historical and artistic purposes. Handle all content with respect for the artists and the communities involved.