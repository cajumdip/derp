# Quick Start Guide - Wayback Machine Scraper

This guide will help you get started with the Cojumpendium Wayback Machine scraper quickly.

## Important Note

⚠️ **This scraper will take DAYS or WEEKS to complete due to necessary rate limiting.** This is intentional to avoid being blocked by the Internet Archive. Do not try to speed it up.

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

## Basic Workflow

### 1. Initialize the Scraper
```bash
python -m cojumpendium_scraper init
```

This creates:
- `config.yaml` - Configuration file
- `cojumpendium.db` - SQLite database
- `downloads/` - Directory for downloaded media
- `pages/` - Directory for cached HTML pages
- `exports/` - Directory for exported data

### 2. Customize Configuration (Optional)

Edit `config.yaml` to customize:
- Search phrases (default: "Cojum Dip", "cojumdip", "bkaraca", "Bora Karaca")
- Date range (default: 2004-2012)
- Rate limiting settings (⚠️ DO NOT reduce these!)
- User agents

### 3. Search Wayback Machine

#### Search using all methods for all phrases:
```bash
python -m cojumpendium_scraper search
```

#### Search specific phrase:
```bash
python -m cojumpendium_scraper search --phrase "Cojum Dip"
python -m cojumpendium_scraper search --phrase "bkaraca"
```

#### Search using specific method:
```bash
python -m cojumpendium_scraper search --method cdx
python -m cojumpendium_scraper search --method calendar
python -m cojumpendium_scraper search --method fulltext
python -m cojumpendium_scraper search --method archive_search
```

#### Resume interrupted search:
```bash
python -m cojumpendium_scraper search --resume
```

### 4. Fetch and Analyze Discovered Pages

After searching, fetch the discovered URLs:
```bash
python -m cojumpendium_scraper fetch
```

This will:
- Download archived HTML pages
- Analyze content for target phrases
- Extract media URLs
- Save everything to the database

### 5. Check Progress

View statistics:
```bash
python -m cojumpendium_scraper stats
```

Check rate limiting status:
```bash
python -m cojumpendium_scraper rate-status
```

### 6. Export Results

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

#### `search`
Search Wayback Machine for content.

Options:
- `-p, --phrase TEXT` - Specific phrase to search
- `-m, --method [cdx|calendar|fulltext|archive_search|all]` - Search method (default: all)
- `--resume` - Resume from previous progress

#### `fetch`
Fetch and analyze discovered pages.

Options:
- `-l, --limit INTEGER` - Maximum URLs to fetch (default: 100)

#### `stats`
Show database statistics including:
- Discovered URLs by status
- Discovered URLs by search phrase
- Media by type
- Search progress
- Recent request statistics

#### `rate-status`
Show rate limiting status and recent errors.

#### `export`
Export scraped data.

Options:
- `-f, --format [json|csv|html|all]` - Export format (default: all)

## Search Methods Explained

### CDX Server API
Fast URL-based searches with wildcard matching. Good for finding known sites.

### Calendar Captures API
Granular day-by-day snapshot discovery for specific known URLs.

### Full-text Search
HTML parsing of Wayback's search results. Slower but finds content in any archived page.

### Archive.org Search
Searches uploaded audio/video/documents in Archive.org's collection.

## Rate Limiting - CRITICAL

The scraper includes aggressive rate limiting:

- **5-15 second delays** between requests
- **Random jittering** to avoid pattern detection
- **Exponential backoff** on errors (30s → 10 minutes)
- **100 requests/hour** maximum
- **Cooldown periods** (3 minutes every 50 requests)

**Do NOT modify these settings** unless you want to be blocked!

## Expected Timeline

For reference, here's what to expect:

- **Single search method, single phrase**: 2-4 days
- **All methods, single phrase**: 1-2 weeks
- **All methods, all phrases**: 3-4 weeks
- **Full search + fetch**: 1-2 months

**This is normal and necessary.** Use the `--resume` flag if interrupted.

## Tips for Success

1. **Be Patient** - Let it run for days/weeks
   
2. **Use screen/tmux** for long sessions:
   ```bash
   screen -S wayback
   python -m cojumpendium_scraper search
   # Ctrl+A, D to detach
   screen -r wayback  # to reattach
   ```

3. **Monitor Progress** regularly:
   ```bash
   python -m cojumpendium_scraper stats
   ```

4. **Resume if Interrupted**:
   ```bash
   python -m cojumpendium_scraper search --resume
   ```

5. **Check Logs** for details:
   ```bash
   tail -f scraper.log
   ```

6. **Export Periodically** to save progress:
   ```bash
   python -m cojumpendium_scraper export
   ```

## Troubleshooting

### "Rate limit exceeded" or 429/403 errors
- **This is normal!** The scraper will automatically backoff
- Check `rate-status` to see current state
- DO NOT reduce rate limiting settings

### Search taking too long
- **This is expected and intentional**
- Use `--resume` to continue interrupted searches
- Monitor progress with `stats` command

### "Database not found"
```bash
python -m cojumpendium_scraper init
```

### Import errors
```bash
pip install -r requirements.txt --upgrade
```

### Out of disk space
- Check the `pages/` directory size
- Consider clearing old cached HTML files
- Exported data is kept in `exports/`

## Example Complete Workflow

```bash
# 1. Setup
python -m cojumpendium_scraper init

# 2. Optional: Edit config.yaml to customize

# 3. Start comprehensive search (will take weeks!)
python -m cojumpendium_scraper search

# In another terminal, monitor progress:
watch -n 300 'python -m cojumpendium_scraper stats'

# 4. After search completes, fetch pages
python -m cojumpendium_scraper fetch

# 5. Check what was found
python -m cojumpendium_scraper stats

# 6. Export everything
python -m cojumpendium_scraper export

# 7. Review HTML report
open exports/report_*.html
```

## Recommended Approach for Beginners

Start with a single phrase and method:

```bash
# Initialize
python -m cojumpendium_scraper init

# Test with one phrase and method (takes 2-4 days)
python -m cojumpendium_scraper search --phrase "cojumdip" --method cdx

# Monitor progress daily
python -m cojumpendium_scraper stats

# Once complete, fetch the discovered URLs
python -m cojumpendium_scraper fetch

# Export results
python -m cojumpendium_scraper export

# If results look good, scale up to all phrases and methods
python -m cojumpendium_scraper search  # all phrases, all methods
```

## Next Steps

- Review the main README.md for detailed documentation
- Understand the rate limiting configuration
- Plan for long-term scraping (weeks/months)
- Share your findings with the Cojumpendium research group!

## Remember

🐢 **Slow and steady wins the race.** This scraper is designed for comprehensive, patient archival research, not quick results. Respect the Internet Archive and you'll find amazing lost content!
