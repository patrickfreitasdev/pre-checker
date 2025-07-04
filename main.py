#!/usr/bin/env python3
"""
Main CLI interface for Website Optimization Pre-Check Tool
"""

import sys
import argparse
import logging
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from website_analyzer import WebsiteAnalyzer
from config import URL_CONFIG

console = Console()

def validate_urls(urls: List[str]) -> List[str]:
    """
    Validate and clean URLs
    
    Args:
        urls (List[str]): List of URLs to validate
        
    Returns:
        List[str]: Validated URLs
    """
    valid_urls = []
    
    for url in urls:
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic validation
        if any(scheme in url for scheme in URL_CONFIG['allowed_schemes']):
            valid_urls.append(url)
        else:
            console.print(f"[red]Invalid URL: {url}[/red]")
    
    return valid_urls

def get_urls_interactive() -> List[str]:
    """
    Get URLs interactively from user
    
    Returns:
        List[str]: List of URLs
    """
    console.print(Panel.fit(
        "[bold blue]Website Optimization Pre-Check Tool[/bold blue]\n"
        "Enter up to 4 URLs to analyze (one per line).\n"
        "Press Enter twice when done.",
        title="URL Input"
    ))
    
    urls = []
    while len(urls) < URL_CONFIG['max_urls']:
        url = console.input(f"[cyan]URL {len(urls) + 1}:[/cyan] ").strip()
        
        if not url:
            if urls:  # Allow empty line to finish
                break
            else:
                console.print("[yellow]Please enter at least one URL[/yellow]")
                continue
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        urls.append(url)
    
    return urls

def display_results(analyzer: WebsiteAnalyzer):
    """
    Display analysis results in a formatted table
    
    Args:
        analyzer: WebsiteAnalyzer instance
    """
    results = analyzer.get_results()
    
    # Create results table
    table = Table(title="Analysis Results")
    table.add_column("URL", style="cyan", no_wrap=True)
    table.add_column("Desktop Score", style="green")
    table.add_column("Mobile Score", style="green")
    table.add_column("Avg Score", style="yellow")
    table.add_column("Files", style="blue")
    table.add_column("Errors", style="red")
    
    # Calculate totals for averages
    total_desktop_scores = []
    total_mobile_scores = []
    total_files = 0
    total_errors = 0
    url_count = len(results)
    
    for url, url_results in results.items():
        summary = url_results.get('summary', {})
        
        desktop_score = summary.get('desktop_score', 'N/A')
        mobile_score = summary.get('mobile_score', 'N/A')
        avg_score = summary.get('average_score', 'N/A')
        files = summary.get('files_generated', 0)
        errors = summary.get('errors_count', 0)
        
        # Collect scores for averages
        if isinstance(desktop_score, (int, float)):
            total_desktop_scores.append(desktop_score)
        if isinstance(mobile_score, (int, float)):
            total_mobile_scores.append(mobile_score)
        
        total_files += files
        total_errors += errors
        
        # Format scores
        if isinstance(desktop_score, (int, float)):
            desktop_score = f"{desktop_score}"
        if isinstance(mobile_score, (int, float)):
            mobile_score = f"{mobile_score}"
        if isinstance(avg_score, (int, float)):
            avg_score = f"{avg_score:.1f}"
        
        table.add_row(
            url,
            desktop_score,
            mobile_score,
            avg_score,
            str(files),
            str(errors)
        )
    
    console.print(table)
    
    # Display averages across all URLs
    if url_count > 1:
        avg_desktop = sum(total_desktop_scores) / len(total_desktop_scores) if total_desktop_scores else 0
        avg_mobile = sum(total_mobile_scores) / len(total_mobile_scores) if total_mobile_scores else 0
        overall_avg = (avg_desktop + avg_mobile) / 2 if total_desktop_scores and total_mobile_scores else 0
        
        console.print(f"\n[bold blue]Overall Averages (across {url_count} URLs):[/bold blue]")
        console.print(f"  Desktop Score: {avg_desktop:.1f}")
        console.print(f"  Mobile Score: {avg_mobile:.1f}")
        console.print(f"  Overall Average: {overall_avg:.1f}")
        console.print(f"  Total Files Generated: {total_files}")
        console.print(f"  Total Errors: {total_errors}")
    
    # Display output directory
    output_dir = analyzer.get_output_directory()
    console.print(f"\n[bold green]Output Directory:[/bold green] {output_dir}")
    console.print(f"[bold green]Summary Report:[/bold green] {output_dir}/summary_report.txt")
    console.print(f"[bold green]Log File:[/bold green] {output_dir}/analysis.log")

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Website Optimization Pre-Check Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --urls "https://example.com,https://google.com"
  python main.py --urls "example.com,google.com,github.com,wikipedia.org"
  python main.py  # Interactive mode
        """
    )
    
    parser.add_argument(
        '--urls',
        type=str,
        help='Comma-separated list of URLs to analyze (max 4)'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Module-specific flags
    parser.add_argument(
        '--score',
        action='store_true',
        help='Run PageSpeed analysis only'
    )
    
    parser.add_argument(
        '--screenshot',
        action='store_true',
        help='Take screenshots only'
    )
    
    parser.add_argument(
        '--record',
        action='store_true',
        help='Record videos only'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all modules (default behavior)'
    )
    
    args = parser.parse_args()
    
    # Setup console
    console.print(Panel.fit(
        "[bold blue]Website Optimization Pre-Check Tool[/bold blue]\n"
        "Automated website testing with video recording, screenshots, and PageSpeed analysis",
        title="Welcome"
    ))
    
    # Get URLs
    if args.urls:
        urls = [url.strip() for url in args.urls.split(',')]
    else:
        urls = get_urls_interactive()
    
    # Validate URLs
    if not urls:
        console.print("[red]No valid URLs provided. Exiting.[/red]")
        sys.exit(1)
    
    urls = validate_urls(urls)
    if not urls:
        console.print("[red]No valid URLs after validation. Exiting.[/red]")
        sys.exit(1)
    
    # Limit to max URLs
    if len(urls) > URL_CONFIG['max_urls']:
        console.print(f"[yellow]Limiting to {URL_CONFIG['max_urls']} URLs[/yellow]")
        urls = urls[:URL_CONFIG['max_urls']]
    
    # Display URLs to be analyzed
    console.print(f"\n[bold]Analyzing {len(urls)} URLs:[/bold]")
    for i, url in enumerate(urls, 1):
        console.print(f"  {i}. {url}")
    
    # Confirm with user
    if not args.urls:  # Only ask in interactive mode
        confirm = console.input("\n[cyan]Proceed with analysis? (y/N):[/cyan] ").lower()
        if confirm not in ['y', 'yes']:
            console.print("[yellow]Analysis cancelled.[/yellow]")
            sys.exit(0)
    
    # Update headless mode if specified
    if args.headless:
        from config import BROWSER_CONFIG
        BROWSER_CONFIG['headless'] = True
        console.print("[yellow]Running in headless mode[/yellow]")
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine which modules to run
    modules_to_run = []
    if args.score:
        modules_to_run.append('score')
    if args.screenshot:
        modules_to_run.append('screenshot')
    if args.record:
        modules_to_run.append('record')
    if args.all or not modules_to_run:
        modules_to_run = ['score', 'screenshot', 'record']  # Default: run all
    
    console.print(f"[cyan]Running modules: {', '.join(modules_to_run)}[/cyan]")
    
    # Create analyzer
    try:
        analyzer = WebsiteAnalyzer(urls, modules=modules_to_run)
    except Exception as e:
        console.print(f"[red]Error initializing analyzer: {str(e)}[/red]")
        sys.exit(1)
    
    # Run analysis with progress indicator
    console.print("\n[bold green]Starting analysis...[/bold green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing websites...", total=None)
        
        try:
            results = analyzer.analyze_all_urls()
            progress.update(task, description="Analysis completed!")
        except KeyboardInterrupt:
            console.print("\n[yellow]Analysis interrupted by user.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Error during analysis: {str(e)}[/red]")
            sys.exit(1)
    
    # Display results
    console.print("\n[bold green]Analysis completed![/bold green]")
    display_results(analyzer)
    
    # Show next steps
    console.print(Panel.fit(
        "[bold]Next Steps:[/bold]\n"
        "• Review the generated videos in the videos/ directory\n"
        "• Check screenshots in the screenshots/ directory\n"
        "• View PageSpeed results in the pagespeed/ directory\n"
        "• Read the summary report for overall performance insights",
        title="What's Next?"
    ))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user. Exiting.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        sys.exit(1) 