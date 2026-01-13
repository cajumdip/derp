# Quick Start Guide

This guide will help you get started with the Cojumpendium scraper quickly.

## Installation

```bash
# Clone the repository
git clone https://github.com/cajumdip/derp.git
cd derp

# Install dependencies
pip install -r requirements.txt

# Initialize the scraper
python -m cojumpendium_scraper init
```

## Basic Usage

### 1. Initialize the Scraper
```bash
python -m cojumpendium_scraper init
```

This creates:
- `config.yaml` - Configuration file
- `cojumpendium.db` - SQLite database
- `downloads/` - Directory for downloaded media
- `exports/` - Directory for exported data

### 2. Customize Configuration (Optional)

Edit `config.yaml` to customize:
- Search terms
- Date ranges
- Platform settings
- Download settings
- Rate limits

### 3. Run the Scraper

#### Scrape all platforms:
```bash
python -m cojumpendium_scraper scrape
```

#### Scrape specific platforms:
```bash
python -m cojumpendium_scraper scrape --platform wayback
python -m cojumpendium_scraper scrape --platform myspace --platform youtube
```

#### Dry run (test without saving):
```bash
python -m cojumpendium_scraper scrape --dry-run
```

### 4. Check Progress

View statistics:
```bash
python -m cojumpendium_scraper stats
```

### 5. Export Results

Export all formats:
```bash
python -m cojumpendium_scraper export
```

Export specific format:
```bash
python -m cojumpendium_scraper export --format json
python -m cojumpendium_scraper export --format csv
python -m cojumpendium_scraper export --format html
```

## Command Reference

### Global Options
- `-c, --config PATH` - Use custom config file
- `-v, --verbose` - Enable verbose output
- `--help` - Show help message

### Commands

#### `init`
Initialize configuration and database.

#### `scrape`
Run the scraper to discover lost media.

Options:
- `-p, --platform NAME` - Scrape specific platform (can be used multiple times)
- `--dry-run` - Test without saving to database

#### `stats`
Show database statistics including:
- URLs by status (pending, completed, error)
- Media files by type (image, video, audio)
- Total storage used
- URLs by platform

#### `export`
Export scraped data.

Options:
- `-f, --format FORMAT` - Export format: json, csv, html, or all (default: all)

## Tips

1. **Start with a dry run** to see what will be scraped:
   ```bash
   python -m cojumpendium_scraper scrape --dry-run --platform wayback
   ```

2. **Use verbose mode** for debugging:
   ```bash
   python -m cojumpendium_scraper -v scrape
   ```

3. **Check logs** for detailed information:
   ```bash
   tail -f scraper.log
   ```

4. **Export regularly** to save your progress:
   ```bash
   python -m cojumpendium_scraper export
   ```

## Platform Priority

For finding Cojum Dip lost media, prioritize these platforms:

1. **Wayback Machine** - Primary source for archived content
2. **MySpace** - Old music profiles and players
3. **YouTube** - Video content
4. **Last.fm** - Scrobbles and artist info
5. **Soundcloud** - Audio tracks
6. **Flickr** - Photo archives

## Search Terms Priority

The configuration includes search terms with these priorities:

**HIGH PRIORITY:**
- "Turk Off"
- "2010 Remix"

**MEDIUM PRIORITY:**
- "Cojum Dip"
- "Bora Karaca"
- Band member personas

**LOW PRIORITY:**
- Venue combinations
- Related searches

## Troubleshooting

### No results found
- Check your internet connection
- Verify the date range in config.yaml
- Try different search terms
- Some archived content may no longer be available

### Rate limit errors
- Increase `request_delay` in config.yaml
- Reduce `max_concurrent` in config.yaml

### Import errors
```bash
pip install -r requirements.txt --upgrade
```

### Database locked
```bash
# Close any other processes using the database
# Or use a different database file in config.yaml
```

## Example Workflow

```bash
# 1. Setup
python -m cojumpendium_scraper init

# 2. Edit config.yaml to customize settings

# 3. Test with dry run
python -m cojumpendium_scraper -v scrape --dry-run --platform wayback

# 4. Run actual scrape
python -m cojumpendium_scraper scrape --platform wayback

# 5. Check progress
python -m cojumpendium_scraper stats

# 6. Export results
python -m cojumpendium_scraper export

# 7. Review HTML report
open exports/report_*.html
```

## Next Steps

- Review the main README.md for detailed documentation
- Check the configuration options in config.yaml
- Explore the scraped data in the exports directory
- Share your findings with the Cojumpendium research group!
