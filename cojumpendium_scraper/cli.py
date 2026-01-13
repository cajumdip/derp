"""Command-line interface for Cojumpendium scraper."""

import click
import asyncio
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import logging

from .config import Config
from .database import Database
from .utils.logging import setup_logging
from .utils.http import HTTPClient, RateLimiter
from .scrapers.wayback import WaybackScraper
from .scrapers.myspace import MySpaceScraper
from .scrapers.soundcloud import SoundcloudScraper
from .scrapers.youtube import YouTubeScraper
from .extractors.images import ImageExtractor
from .extractors.video import VideoExtractor
from .extractors.audio import AudioExtractor
from .exporters.json_export import JSONExporter
from .exporters.csv_export import CSVExporter
from .exporters.html_report import HTMLReporter


console = Console()


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """Cojumpendium Lost Media Scraper - DERP (Discovering Elusive Recordings Project)"""
    # Initialize configuration
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config(config)
    
    # Setup logging
    log_level = 'DEBUG' if verbose else ctx.obj['config'].get('general', 'log_level', default='INFO')
    log_file = ctx.obj['config'].get('general', 'log_file', default='./scraper.log')
    setup_logging(log_level, log_file)
    
    # Ensure directories exist
    ctx.obj['config'].ensure_directories()


@cli.command()
@click.option('--platform', '-p', multiple=True, 
              help='Specific platform to scrape (can be used multiple times)')
@click.option('--dry-run', is_flag=True, help='Dry run - don\'t save to database')
@click.pass_context
def scrape(ctx, platform, dry_run):
    """Run the scraper to discover lost media."""
    config = ctx.obj['config']
    
    console.print("[bold green]Starting Cojumpendium Scraper...[/bold green]")
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No data will be saved[/yellow]")
    
    # Run async scraping
    asyncio.run(_run_scraper(config, platform, dry_run))


async def _run_scraper(config: Config, platforms: tuple, dry_run: bool):
    """Run the scraper asynchronously.
    
    Args:
        config: Configuration object
        platforms: Tuple of platform names to scrape
        dry_run: Whether this is a dry run
    """
    # Initialize database
    db_path = config.get('general', 'database', default='./cojumpendium.db')
    db = Database(db_path) if not dry_run else None
    
    # Initialize HTTP client
    user_agent = config.get('http', 'user_agent')
    timeout = config.get('http', 'timeout', default=30)
    max_retries = config.get('http', 'max_retries', default=3)
    rate_limit = config.get('wayback', 'rate_limit', default=30)
    
    rate_limiter = RateLimiter(requests_per_minute=rate_limit)
    
    async with HTTPClient(user_agent, timeout, max_retries, rate_limiter) as http:
        # Get search terms
        search_terms = config.get('search', 'terms', default=[])
        
        # Initialize scrapers
        scrapers = []
        
        if not platforms or 'wayback' in platforms:
            scrapers.append(WaybackScraper(config, db, http))
        if not platforms or 'myspace' in platforms:
            scrapers.append(MySpaceScraper(config, db, http))
        if not platforms or 'soundcloud' in platforms:
            scrapers.append(SoundcloudScraper(config, db, http))
        if not platforms or 'youtube' in platforms:
            scrapers.append(YouTubeScraper(config, db, http))
        
        # Run scrapers
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for scraper in scrapers:
                task = progress.add_task(
                    f"Scraping {scraper.platform_name}...",
                    total=None
                )
                
                try:
                    results = await scraper.run(search_terms=search_terms)
                    progress.update(task, completed=True)
                    
                    console.print(
                        f"[green]✓[/green] {scraper.platform_name}: "
                        f"{results['urls_found']} URLs found, "
                        f"{results['urls_scraped']} scraped, "
                        f"{results['errors']} errors"
                    )
                    
                except Exception as e:
                    progress.update(task, completed=True)
                    console.print(f"[red]✗[/red] {scraper.platform_name}: {e}")
    
    if db:
        db.close()
    
    console.print("\n[bold green]Scraping complete![/bold green]")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    config = ctx.obj['config']
    db_path = config.get('general', 'database', default='./cojumpendium.db')
    
    if not Path(db_path).exists():
        console.print(f"[red]Database not found: {db_path}[/red]")
        return
    
    with Database(db_path) as db:
        statistics = db.get_statistics()
        
        # Create statistics table
        table = Table(title="Cojumpendium Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # URLs by status
        table.add_row("[bold]URLs by Status[/bold]", "")
        for status, count in statistics.get('urls_by_status', {}).items():
            table.add_row(f"  {status}", str(count))
        
        # Media by type
        table.add_row("[bold]Media Files by Type[/bold]", "")
        for media_type, count in statistics.get('media_by_type', {}).items():
            table.add_row(f"  {media_type}", str(count))
        
        # Storage
        total_bytes = statistics.get('total_storage_bytes', 0)
        total_mb = total_bytes / (1024 * 1024)
        table.add_row("[bold]Total Storage[/bold]", f"{total_mb:.2f} MB")
        
        # Platforms
        table.add_row("[bold]URLs by Platform[/bold]", "")
        for platform, count in statistics.get('urls_by_platform', {}).items():
            table.add_row(f"  {platform}", str(count))
        
        console.print(table)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'html', 'all']),
              default='all', help='Export format')
@click.pass_context
def export(ctx, format):
    """Export scraped data."""
    config = ctx.obj['config']
    db_path = config.get('general', 'database', default='./cojumpendium.db')
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
    db_path = config.get('general', 'database', default='./cojumpendium.db')
    Database(db_path)
    console.print(f"[green]✓[/green] Initialized database: {db_path}")
    
    # Create directories
    config.ensure_directories()
    console.print("[green]✓[/green] Created required directories")
    
    console.print("\n[bold green]Initialization complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Edit config.yaml to customize settings")
    console.print("  2. Run 'python -m cojumpendium_scraper scrape' to start scraping")


if __name__ == '__main__':
    cli(obj={})
