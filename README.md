# Cojum Dip Lost Media Scraper (DERP)

**D**iscovering **E**lusive **R**ecordings **P**roject

A comprehensive Wayback Machine scraper for the Cojumpendium research group to find lost media from the band Cojum Dip (2004-2011).

## About

This specialized scraping tool is **100% focused on searching the Internet Archive's Wayback Machine** for archived photos, videos, audio, and mentions of Cojum Dip. It uses multiple search methods to ensure comprehensive coverage of all archived content.

### Background

Cojum Dip is an experimental band founded by Bora Karaca around 2004 at the University of Michigan. The band has significant lost media from the pre-2011 era. The Cojumpendium research group has the founder's full support for this archival effort, which will help with the current album rollout.

**Priority target**: Finding "Turk Off" / "2010 Remix" release

## Why Wayback Machine Only?

After analysis, we determined that the Wayback Machine is the single most comprehensive source for historical content. The Cojumpendium research group has already archived everything available on Archive.org itself, so this scraper focuses exclusively on **Wayback Machine snapshots** of archived web pages from 2004-2011.

Rather than searching Archive.org uploads (which the group already has), this tool searches for:

1. **CDX Server API** - Fast URL-based searches with wildcard matching + platform-specific URL patterns
2. **Calendar Captures API** - Granular day-by-day snapshot discovery
3. **Full-text Search** - HTML parsing of Wayback search results

**Date Filter**: All searches are limited to **2004-2011 ONLY** - nothing after 2011 is included.

## Features

### Core Capabilities
- **Multiple Wayback Search Methods** - Comprehensive coverage using 3 different APIs (CDX, Calendar, Full-text)
- **Date Filtering** - All searches limited to 2004-2011 snapshots ONLY
- **URL Pattern Search** - Search specific platforms (MySpace, Soundcloud, YouTube, etc.)
- **Aggressive Rate Limiting** - Built-in protection against blocks with exponential backoff
- **Smart Session Management** - Resume interrupted searches from where you left off
- **Content Analysis** - Automatic phrase detection in archived pages
- **Enhanced Media Extraction** - Detection of images, videos, audio, Flash (SWF), YouTube embeds, MySpace music, Soundcloud
- **Request Jittering** - Random delays to avoid detection
- **User-Agent Rotation** - Realistic browser identification
- **SQLite Database** - Track all discovered URLs and their status
- **Export Options** - JSON, CSV, and HTML report generation

### Search Targets
The scraper searches for these phrases (2004-2011 snapshots only):

**Primary Targets:**
- "Cojum Dip"
- "cojumdip"
- "bkaraca"
- "Bora Karaca"

**High Priority:**
- "Turk Off" (original 2008 EP)
- "2010 Remix" (lost Soundcloud playlist)

**Band Members:**
- "Bodur the Clumsy"
- "Udabn the Feared"
- "Captain No the Love Machine"
- "Mumutits the Sour"
- "Oktabis the Keeper"

**Related:**
- "Tally Hall Bora"
- "Anthropomorphic Bible Assault"
- "Greatest Demo CD in the Universe"
- Venues: "Blind Pig", "Duderstadt Center"

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
- Create required directories (downloads, pages, exports)

## Configuration

Edit `config.yaml` to customize the scraper behavior:

```yaml
# Search configuration - REQUIRED phrases
search:
  phrases:
    - "Cojum Dip"
    - "cojumdip"
    - "bkaraca"
    - "Bora Karaca"
    - "Turk Off"
    - "2010 Remix"
    # ... see config.yaml for all 17 phrases
  
  # URL patterns for CDX search
  url_patterns:
    - "myspace.com/cojumdip"
    - "soundcloud.com/cojumdip"
    - "youtube.com/*cojum*"
    # ... see config.yaml for all 16 patterns
  
  date_range:
    start: 2004
    end: 2011  # NOTHING AFTER 2011

# Rate limiting (CRITICAL for avoiding blocks)
rate_limiting:
  min_delay: 5          # Minimum seconds between requests
  max_delay: 15         # Maximum delay
  jitter: 3             # Random variance
  backoff_base: 30      # Initial backoff on error
  backoff_max: 600      # Max backoff (10 minutes)
  requests_per_hour: 100
  cooldown_every: 50    # Pause after this many requests
  cooldown_duration: 180 # Pause for 3 minutes
```

See `config.example.yaml` for all available options.

## Usage

### Basic Workflow

1. **Initialize** (first time only)
```bash
python -m cojumpendium_scraper init
```

2. **Search** for archived content (2004-2011 snapshots only)
```bash
# Search using all methods for all phrases
python -m cojumpendium_scraper search

# Search specific phrase
python -m cojumpendium_scraper search --phrase "Turk Off"
python -m cojumpendium_scraper search --phrase "2010 Remix"

# Use specific search method
python -m cojumpendium_scraper search --method cdx
python -m cojumpendium_scraper search --method calendar
python -m cojumpendium_scraper search --method fulltext

# Resume interrupted search
python -m cojumpendium_scraper search --resume
```

3. **Fetch and analyze** discovered pages
```bash
python -m cojumpendium_scraper fetch
```

4. **Check progress**
```bash
python -m cojumpendium_scraper stats
python -m cojumpendium_scraper rate-status
```

5. **Export findings**
```bash
python -m cojumpendium_scraper export --format json
python -m cojumpendium_scraper export --format csv
python -m cojumpendium_scraper export --format html
```

### Available Commands

#### `init`
Initialize configuration and database
```bash
python -m cojumpendium_scraper init
```

#### `search`
Search Wayback Machine for content (2004-2011 snapshots only)
```bash
python -m cojumpendium_scraper search [OPTIONS]

Options:
  --phrase, -p TEXT      Specific phrase to search
  --method, -m [cdx|calendar|fulltext|all]
                        Search method (default: all)
                        Note: archive_search is disabled by default
  --resume              Resume from previous progress
```

#### `fetch`
Fetch and analyze discovered pages
```bash
python -m cojumpendium_scraper fetch [OPTIONS]

Options:
  --limit, -l INTEGER   Maximum URLs to fetch (default: 100)
```

#### `stats`
Show database statistics
```bash
python -m cojumpendium_scraper stats
```

#### `rate-status`
Show rate limiting status
```bash
python -m cojumpendium_scraper rate-status
```

#### `export`
Export scraped data
```bash
python -m cojumpendium_scraper export [OPTIONS]

Options:
  --format, -f [json|csv|html|all]
                        Export format (default: all)
```

## Project Structure

```
cojumpendium_scraper/
├── __init__.py           # Package initialization
├── __main__.py           # CLI entry point
├── cli.py                # Command-line interface
├── config.py             # Configuration management
├── database.py           # SQLite database operations
├── wayback/              # Wayback Machine scrapers
│   ├── cdx.py            # CDX Server API
│   ├── calendar.py       # Calendar Captures API
│   ├── fulltext.py       # Full-text search scraping
│   ├── archive_search.py # Archive.org search API
│   └── fetcher.py        # Page fetching with analysis
├── extractors/           # Media extraction
│   ├── content.py        # Content/phrase analyzer
│   ├── media.py          # Base media extractor
│   ├── images.py         # Image extractor
│   ├── video.py          # Video extractor
│   └── audio.py          # Audio extractor
├── utils/                # Utility modules
│   ├── http.py           # HTTP client
│   ├── rate_limiter.py   # Advanced rate limiting
│   ├── user_agents.py    # UA rotation
│   ├── hashing.py        # File hashing
│   └── logging.py        # Logging configuration
└── exporters/            # Data export
    ├── json_export.py    # JSON exporter
    ├── csv_export.py     # CSV exporter
    └── html_report.py    # HTML report generator
```

## Database Schema

### `discovered_urls`
Tracks URLs discovered from Wayback searches
- Archive URL and original URL
- Archive timestamp
- Search phrase that found it
- Status (pending/fetched/analyzed/error)
- Content hash

### `media`
Media found on archived pages
- URL to media file
- Media type (image/video/audio)
- Local download path
- File hash

### `search_progress`
Tracks progress of searches for resumption
- Search phrase and method
- Last offset/timestamp processed
- Completion status

### `request_log`
Logs all HTTP requests for rate limiting
- Request URL
- Status code
- Success/failure
- Timestamp

## Rate Limiting - CRITICAL

The Wayback Machine **WILL block aggressive scrapers**. This tool includes comprehensive rate limiting:

- **5-15 second delays** between requests (with jittering)
- **Exponential backoff** on 403/429/503 errors (starts at 30s, doubles up to 10 minutes)
- **Hourly limits** (default: 100 requests/hour)
- **Cooldown periods** (pause for 3 minutes after every 50 requests)
- **Request logging** for monitoring
- **Session persistence** - resume where you left off

### Expected Runtime

**This scraper will take days or weeks to complete**. This is intentional and necessary to avoid being blocked. The comprehensive search with rate limiting means:

- ~100-300 requests per day
- Multiple days per search method
- Weeks for complete coverage of all phrases and methods

**Do not try to speed this up**. You will be blocked and lose all progress.

## Tips for Effective Scraping

1. **Be Patient** - Let the scraper run for days/weeks
2. **Monitor Progress** - Use `stats` and `rate-status` commands regularly
3. **Resume Capability** - Use `--resume` if interrupted
4. **Run in Background** - Use `screen` or `tmux` for long-running sessions
5. **Export Periodically** - Save your progress with `export` command
6. **Check Logs** - Review `scraper.log` for detailed information
7. **Respect Rate Limits** - Don't modify rate limiting settings unless necessary

## Troubleshooting

### Common Issues

**"Database not found"**
- Run `python -m cojumpendium_scraper init` to initialize

**"Rate limit exceeded" or 429/403 errors**
- This is normal - the scraper will automatically backoff
- Check logs to see current backoff time
- Do NOT reduce rate limiting settings

**"Search taking too long"**
- This is expected and intentional
- Use `--resume` to continue interrupted searches
- Monitor progress with `stats` command

**Import errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`

## Legal and Ethical Considerations

- This tool respects rate limits and implements aggressive throttling
- Archives content for historical preservation purposes
- Has explicit permission from the band founder (Bora Karaca)
- Complies with Archive.org's terms of service
- Uses reasonable User-Agent strings identifying the project

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Bora Karaca and Cojum Dip for supporting this archival effort
- The Cojumpendium research group
- Archive.org for preserving internet history

## Contact

For questions or to contribute, please open an issue on GitHub.

---

**Remember**: The goal is to preserve lost media for historical and artistic purposes. Be patient, respect rate limits, and handle all content with respect for the artists and the communities involved.