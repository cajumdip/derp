"""Command-line interface for Cojumpendium scraper."""

import click
import asyncio
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
import logging
import aiohttp

from .config import Config
from .database import Database
from .utils.logging import setup_logging
from .utils.rate_limiter import AdaptiveRateLimiter
from .utils.user_agents import UserAgentRotator, DEFAULT_USER_AGENTS
from .wayback.cdx import CDXScraper
from .wayback.calendar import CalendarScraper
from .wayback.fulltext import FullTextScraper
from .wayback.archive_search import ArchiveSearchScraper
from .wayback.fetcher import PageFetcher
from .exporters.json_export import JSONExporter
from .exporters.csv_export import CSVExporter
from .exporters.html_report import HTMLReporter


console = Console()


class AsyncHTTPClient:
    """Simple async HTTP client wrapper."""
    
    def __init__(self, user_agent_rotator):
        self.user_agent_rotator = user_agent_rotator
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_text(self, url: str) -> str:
        """Get text content from URL with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            Text content
            
        Raises:
            aiohttp.ClientError: On network/HTTP errors with meaningful message
        """
        headers = {'User-Agent': self.user_agent_rotator.get_random()}
        try:
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientTimeout as e:
            raise aiohttp.ClientError(f"Request timed out for {url}: {e}")
        except aiohttp.ClientResponseError as e:
            raise aiohttp.ClientError(f"HTTP {e.status} error for {url}: {e.message}")
        except aiohttp.ClientConnectionError as e:
            raise aiohttp.ClientError(f"Connection failed for {url}: {e}")
        except Exception as e:
            raise aiohttp.ClientError(f"Unexpected error fetching {url}: {e}")
    
    async def get_json(self, url: str):
        """Get JSON content from URL with error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            JSON data
            
        Raises:
            aiohttp.ClientError: On network/HTTP/parsing errors with meaningful message
        """
        headers = {'User-Agent': self.user_agent_rotator.get_random()}
        try:
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientTimeout as e:
            raise aiohttp.ClientError(f"Request timed out for {url}: {e}")
        except aiohttp.ClientResponseError as e:
            raise aiohttp.ClientError(f"HTTP {e.status} error for {url}: {e.message}")
        except aiohttp.ClientConnectionError as e:
            raise aiohttp.ClientError(f"Connection failed for {url}: {e}")
        except Exception as e:
            raise aiohttp.ClientError(f"Unexpected error fetching {url}: {e}")


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Cojumpendium Wayback Machine Scraper - Find ALL Cojum Dip mentions in Internet Archive"""
    # Initialize configuration
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config(config)
    
    # Setup logging
    log_level = 'DEBUG' if verbose else ctx.obj['config'].get('logging', 'level', default='INFO')
    log_file = ctx.obj['config'].get('logging', 'file', default='./scraper.log')
    setup_logging(log_level, log_file)
    
    # Ensure directories exist
    ctx.obj['config'].ensure_directories()


@cli.command()
@click.option('--phrase', '-p', help='Specific phrase to search (if not specified, searches all configured phrases)')
@click.option('--method', '-m', type=click.Choice(['cdx', 'calendar', 'fulltext', 'archive_search', 'all']),
              default='all', help='Search method to use')
@click.option('--resume', is_flag=True, help='Resume from previous progress')
@click.pass_context
def search(ctx, phrase, method, resume):
    """Search Wayback Machine for Cojum Dip content."""
    config = ctx.obj['config']
    
    if phrase:
        console.print(f"[bold green]Searching for: {phrase}[/bold green]")
        phrases = [phrase]
    else:
        phrases = config.get('search', 'phrases', default=[
            "Cojum Dip", "cojumdip", "bkaraca", "Bora Karaca"
        ])
        console.print(f"[bold green]Searching for {len(phrases)} phrases[/bold green]")
    
    console.print(f"[bold]Method:[/bold] {method}")
    if resume:
        console.print("[yellow]Resuming from previous progress[/yellow]")
    
    # Run async search
    asyncio.run(_run_search(config, phrases, method, resume))


async def _run_search(config: Config, phrases: list, method: str, resume: bool):
    """Run the search asynchronously."""
    db = Database(config.get('storage', 'database', default='./cojumpendium.db'))
    
    # Initialize rate limiter
    rate_config = {
        'min_delay': config.get('rate_limiting', 'min_delay', default=5),
        'max_delay': config.get('rate_limiting', 'max_delay', default=15),
        'jitter': config.get('rate_limiting', 'jitter', default=3),
        'backoff_base': config.get('rate_limiting', 'backoff_base', default=30),
        'backoff_max': config.get('rate_limiting', 'backoff_max', default=600),
        'requests_per_hour': config.get('rate_limiting', 'requests_per_hour', default=100),
        'cooldown_every': config.get('rate_limiting', 'cooldown_every', default=50),
        'cooldown_duration': config.get('rate_limiting', 'cooldown_duration', default=180)
    }
    rate_limiter = AdaptiveRateLimiter(rate_config)
    
    # Initialize user agent rotator
    user_agents = config.get('user_agents', default=DEFAULT_USER_AGENTS)
    ua_rotator = UserAgentRotator(user_agents)
    
    # Initialize HTTP client
    async with AsyncHTTPClient(ua_rotator) as http_client:
        
        # Initialize scrapers based on method
        scrapers = []
        
        if method in ['cdx', 'all']:
            scrapers.append(('CDX Server API', CDXScraper(config, db, http_client, rate_limiter)))
        if method in ['calendar', 'all']:
            scrapers.append(('Calendar API', CalendarScraper(config, db, http_client, rate_limiter)))
        if method in ['fulltext', 'all']:
            scrapers.append(('Full-text Search', FullTextScraper(config, db, http_client, rate_limiter)))
        if method in ['archive_search', 'all']:
            # Only include Archive.org search if explicitly enabled in config
            if config.get('wayback', 'methods', 'archive_search', default=False):
                scrapers.append(('Archive.org Search', ArchiveSearchScraper(config, db, http_client, rate_limiter)))
        
        # Run searches
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            
            for phrase in phrases:
                for scraper_name, scraper in scrapers:
                    task = progress.add_task(
                        f"[cyan]{scraper_name}[/cyan]: {phrase}",
                        total=None
                    )
                    
                    try:
                        discovered = await scraper.search(phrase, resume=resume)
                        progress.update(task, completed=True)
                        
                        if discovered > 0:
                            console.print(
                                f"[green]✓[/green] {scraper_name} ({phrase}): "
                                f"{discovered} URLs discovered"
                            )
                        else:
                            console.print(
                                f"[yellow]•[/yellow] {scraper_name} ({phrase}): "
                                f"No new URLs"
                            )
                    except Exception as e:
                        progress.update(task, completed=True)
                        console.print(f"[red]✗[/red] {scraper_name} ({phrase}): {e}")
        
        # Show rate limiter stats
        stats = rate_limiter.get_stats()
        console.print(f"\n[bold]Rate Limiter Stats:[/bold]")
        console.print(f"  Total requests: {stats['total_requests']}")
        console.print(f"  Total errors: {stats['total_errors']}")
        console.print(f"  Error rate: {stats['error_rate']:.1%}")
    
    db.close()
    console.print("\n[bold green]Search complete![/bold green]")


@cli.command()
@click.option('--limit', '-l', type=int, default=100, help='Maximum URLs to fetch')
@click.pass_context
def fetch(ctx, limit):
    """Fetch and analyze discovered pages."""
    config = ctx.obj['config']
    
    console.print(f"[bold green]Fetching up to {limit} pending URLs...[/bold green]")
    
    # Run async fetch
    asyncio.run(_run_fetch(config, limit))


async def _run_fetch(config: Config, limit: int):
    """Run the fetch asynchronously."""
    db = Database(config.get('storage', 'database', default='./cojumpendium.db'))
    
    # Initialize rate limiter
    rate_config = {
        'min_delay': config.get('rate_limiting', 'min_delay', default=5),
        'max_delay': config.get('rate_limiting', 'max_delay', default=15),
        'jitter': config.get('rate_limiting', 'jitter', default=3),
        'backoff_base': config.get('rate_limiting', 'backoff_base', default=30),
        'backoff_max': config.get('rate_limiting', 'backoff_max', default=600),
        'requests_per_hour': config.get('rate_limiting', 'requests_per_hour', default=100),
        'cooldown_every': config.get('rate_limiting', 'cooldown_every', default=50),
        'cooldown_duration': config.get('rate_limiting', 'cooldown_duration', default=180)
    }
    rate_limiter = AdaptiveRateLimiter(rate_config)
    
    # Initialize user agent rotator
    user_agents = config.get('user_agents', default=DEFAULT_USER_AGENTS)
    ua_rotator = UserAgentRotator(user_agents)
    
    # Initialize HTTP client and fetcher
    async with AsyncHTTPClient(ua_rotator) as http_client:
        fetcher = PageFetcher(config, db, http_client, rate_limiter)
        
        stats = await fetcher.fetch_pending_urls(limit=limit)
        
        console.print(f"\n[bold]Fetch Results:[/bold]")
        console.print(f"  Fetched: {stats['fetched']}")
        console.print(f"  Analyzed: {stats['analyzed']}")
        console.print(f"  Errors: {stats['errors']}")
    
    db.close()


@cli.command()
@click.pass_context
def download(ctx):
    """Download media from analyzed pages."""
    config = ctx.obj['config']
    console.print("[yellow]Media download not yet implemented[/yellow]")
    console.print("Media URLs are recorded in the database for manual download")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    config = ctx.obj['config']
    db_path = config.get('storage', 'database', default='./cojumpendium.db')
    
    if not Path(db_path).exists():
        console.print(f"[red]Database not found: {db_path}[/red]")
        return
    
    with Database(db_path) as db:
        statistics = db.get_wayback_statistics()
        
        # Create statistics table
        table = Table(title="Cojumpendium Wayback Scraper Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Discovered URLs by status
        table.add_row("[bold]Discovered URLs by Status[/bold]", "")
        for status, count in statistics.get('discovered_urls_by_status', {}).items():
            table.add_row(f"  {status}", str(count))
        
        # Discovered URLs by phrase
        table.add_row("[bold]Discovered URLs by Phrase[/bold]", "")
        for phrase, count in statistics.get('discovered_urls_by_phrase', {}).items():
            table.add_row(f"  {phrase}", str(count))
        
        # Media by type
        table.add_row("[bold]Media by Type[/bold]", "")
        for media_type, count in statistics.get('media_by_type', {}).items():
            table.add_row(f"  {media_type}", str(count))
        
        # Search progress
        table.add_row("[bold]Search Progress[/bold]", "")
        for progress in statistics.get('search_progress', []):
            status = "✓" if progress.get('completed') else "..."
            table.add_row(
                f"  {status} {progress.get('search_phrase')} ({progress.get('search_method')})",
                f"offset: {progress.get('last_offset', 0)}"
            )
        
        # Request stats
        req_stats = statistics.get('requests_last_hour', {})
        if req_stats:
            table.add_row("[bold]Requests (Last Hour)[/bold]", "")
            table.add_row("  Total", str(req_stats.get('total_requests', 0)))
            table.add_row("  Successful", str(req_stats.get('successful_requests', 0)))
            table.add_row("  Failed", str(req_stats.get('failed_requests', 0)))
        
        console.print(table)


@cli.command(name='rate-status')
@click.pass_context
def rate_status(ctx):
    """Show rate limiting status."""
    config = ctx.obj['config']
    db_path = config.get('storage', 'database', default='./cojumpendium.db')
    
    if not Path(db_path).exists():
        console.print(f"[red]Database not found: {db_path}[/red]")
        return
    
    with Database(db_path) as db:
        recent_requests = db.get_recent_requests(minutes=60)
        
        console.print(f"[bold]Rate Limiting Status[/bold]")
        console.print(f"Requests in last hour: {len(recent_requests)}")
        
        if recent_requests:
            successful = sum(1 for r in recent_requests if r['success'])
            failed = len(recent_requests) - successful
            
            console.print(f"  Successful: {successful}")
            console.print(f"  Failed: {failed}")
            console.print(f"  Success rate: {successful/len(recent_requests):.1%}")
            
            # Show recent errors
            errors = [r for r in recent_requests if not r['success']][:5]
            if errors:
                console.print(f"\n[bold]Recent Errors:[/bold]")
                for err in errors:
                    console.print(f"  {err['timestamp']}: {err['url'][:80]}... (status {err['status_code']})")


@cli.command()
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'html', 'all']),
              default='all', help='Export format')
@click.pass_context
def export(ctx, format):
    """Export scraped data."""
    config = ctx.obj['config']
    db_path = config.get('storage', 'database', default='./cojumpendium.db')
    output_dir = config.get('export', 'output_dir', default='./exports')
    
    if not Path(db_path).exists():
        console.print(f"[red]Database not found: {db_path}[/red]")
        return
    
    with Database(db_path) as db:
        console.print(f"[bold]Exporting data to {output_dir}...[/bold]")
        
        if format in ['json', 'all']:
            exporter = JSONExporter(db, output_dir)
            path = exporter.export()
            console.print(f"[green]✓[/green] JSON export: {path}")
        
        if format in ['csv', 'all']:
            exporter = CSVExporter(db, output_dir)
            paths = exporter.export_all()
            console.print(f"[green]✓[/green] CSV exports: {paths}")
        
        if format in ['html', 'all']:
            reporter = HTMLReporter(db, output_dir)
            path = reporter.generate_report()
            console.print(f"[green]✓[/green] HTML report: {path}")
    
    console.print("[bold green]Export complete![/bold green]")


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize configuration and database."""
    config = ctx.obj['config']
    
    # Create config file if it doesn't exist
    if not Path('config.yaml').exists():
        import shutil
        shutil.copy('config.example.yaml', 'config.yaml')
        console.print("[green]✓[/green] Created config.yaml from example")
    
    # Initialize database
    db_path = config.get('storage', 'database', default='./cojumpendium.db')
    Database(db_path)
    console.print(f"[green]✓[/green] Initialized database: {db_path}")
    
    # Create directories
    config.ensure_directories()
    console.print("[green]✓[/green] Created required directories")
    
    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Edit config.yaml to customize settings")
    console.print("  2. Run 'python -m cojumpendium_scraper search' to start searching")
    console.print("  3. Run 'python -m cojumpendium_scraper fetch' to fetch discovered pages")
    console.print("  4. Run 'python -m cojumpendium_scraper stats' to view progress")
    console.print("\n[yellow]Note: Wayback scraping will take days/weeks due to rate limiting![/yellow]")


if __name__ == '__main__':
    cli(obj={})
