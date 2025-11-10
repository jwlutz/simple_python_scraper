#!/usr/bin/env python3
"""
Site Analysis Tool - Main CLI Interface

A production-ready tool for analyzing website structure and planning scraping projects.
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table

from config_loader import load_config
from main import crawl_site_async
from browser_crawler import crawl_with_browser
from visualizer import create_visualizations
from report_generator import generate_all_reports
from csv_report import write_csv_report


console = Console()


def validate_url(url: str) -> str:
    """Validate and normalize URL."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    
    return url


def create_output_directory(base_url: str, output_base: str) -> Path:
    """Create output directory for this analysis."""
    parsed = urlparse(base_url)
    site_name = parsed.netloc.replace('www.', '').replace('.', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    output_dir = Path(output_base) / f"{site_name}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def setup_argparse() -> argparse.ArgumentParser:
    """Setup command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='Site Analysis Tool - Analyze website structure for planning scraping projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick scan of a site
  %(prog)s https://example.com --preset quick_scan
  
  # Deep analysis with custom settings
  %(prog)s https://example.com --max-pages 500 --max-depth 0
  
  # Analyze with specific concurrency and rate limiting
  %(prog)s https://example.com --max-concurrency 5 --rate-limit 2.0
  
  # Use custom config file
  %(prog)s https://example.com --config my_config.yaml
        """
    )
    
    parser.add_argument('url', help='URL of the website to analyze')
    
    # Configuration
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--preset', type=str, choices=['quick_scan', 'deep_analysis', 'polite_crawl'],
                       help='Use a configuration preset')
    
    # Crawling parameters
    parser.add_argument('--max-pages', type=int, help='Maximum pages to crawl')
    parser.add_argument('--max-concurrency', type=int, help='Maximum concurrent requests')
    parser.add_argument('--max-depth', type=int, help='Maximum crawl depth (0 for unlimited)')
    parser.add_argument('--timeout', type=int, help='Request timeout in seconds')
    parser.add_argument('--max-retries', type=int, help='Maximum retry attempts')
    parser.add_argument('--rate-limit', type=float, help='Requests per second (0 for unlimited)')
    
    # Output options
    parser.add_argument('--output', '-o', type=str, default='output',
                       help='Base output directory (default: output)')
    parser.add_argument('--formats', nargs='+', 
                       choices=['json', 'html', 'csv', 'graph', 'stats', 'all'],
                       default=['all'],
                       help='Output formats to generate')
    parser.add_argument('--no-visualization', action='store_true',
                       help='Skip graph visualization generation')
    
    # Display options
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    # Browser mode
    parser.add_argument('--browser', action='store_true',
                       help='Use browser automation (bypasses bot detection, slower)')
    
    return parser


async def run_analysis(args):
    """Run the site analysis."""
    # Load configuration
    config = load_config(args.config, args.preset)
    
    # Apply CLI overrides
    if args.max_pages:
        config.set('crawling', 'max_pages', args.max_pages)
    if args.max_concurrency:
        config.set('crawling', 'max_concurrency', args.max_concurrency)
    if args.max_depth is not None:
        config.set('analysis', 'max_depth', args.max_depth)
    if args.timeout:
        config.set('crawling', 'timeout', args.timeout)
    if args.max_retries:
        config.set('crawling', 'max_retries', args.max_retries)
    if args.rate_limit is not None:
        config.set('crawling', 'rate_limit', args.rate_limit)
    
    # Validate URL
    try:
        base_url = validate_url(args.url)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    
    # Create output directory
    output_dir = create_output_directory(base_url, args.output)
    
    # Display configuration
    if not args.quiet:
        config_table = Table(title="Analysis Configuration", show_header=True)
        config_table.add_column("Parameter", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Target URL", base_url)
        config_table.add_row("Max Pages", str(config.max_pages))
        config_table.add_row("Max Concurrency", str(config.max_concurrency))
        config_table.add_row("Max Depth", str(config.max_depth) if config.max_depth > 0 else "Unlimited")
        config_table.add_row("Rate Limit", f"{config.rate_limit} req/s" if config.rate_limit > 0 else "Unlimited")
        config_table.add_row("Max Retries", str(config.max_retries))
        config_table.add_row("Output Directory", str(output_dir))
        
        console.print(config_table)
        console.print()
    
    # Run the crawl
    if args.browser:
        console.print(Panel.fit("Starting Site Analysis (Browser Mode)", style="bold blue"))
        console.print("[yellow]Using browser automation - this will be slower but can bypass bot detection[/yellow]\n")
    else:
        console.print(Panel.fit("Starting Site Analysis", style="bold blue"))
    
    try:
        if args.browser:
            # Use browser mode
            page_data = await crawl_with_browser(
                base_url,
                max_pages=config.max_pages,
                max_depth=config.max_depth
            )
        else:
            # Use regular async crawling
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Crawling site...", total=config.max_pages)
                
                page_data = await crawl_site_async(
                    base_url,
                    max_concurrency=config.max_concurrency,
                    max_pages=config.max_pages,
                    max_retries=config.max_retries,
                    retry_delay=config.retry_delay,
                    rate_limit=config.rate_limit
                )
                
                progress.update(task, completed=len(page_data))
        
        console.print(f"[green]Successfully crawled {len(page_data)} pages[/green]")
        
        # Generate reports
        formats = args.formats if 'all' not in args.formats else ['json', 'html', 'csv', 'graph', 'stats']
        
        console.print("\n[bold]Generating reports...[/bold]")
        
        if 'json' in formats or 'html' in formats or 'stats' in formats:
            console.print("  Generating analysis reports...")
            generate_all_reports(page_data, base_url, str(output_dir))
        
        if 'csv' in formats:
            console.print("  Generating CSV report...")
            write_csv_report(page_data, str(output_dir / "report.csv"))
        
        if 'graph' in formats and not args.no_visualization:
            console.print("  Generating graph visualizations...")
            create_visualizations(page_data, base_url, str(output_dir))
        
        # Display summary
        console.print()
        console.print(Panel.fit(
            f"[green]Analysis complete![/green]\n\n"
            f"Results saved to: [cyan]{output_dir}[/cyan]\n"
            f"Open [cyan]{output_dir / 'report.html'}[/cyan] to view the full report.",
            title="Success",
            border_style="green"
        ))
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error during analysis: {e}[/red]")
        if args.verbose:
            console.print_exception()
        return 1


def main():
    """Main entry point."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Run the analysis
    exit_code = asyncio.run(run_analysis(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

