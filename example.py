#!/usr/bin/env python3
"""
Example usage of the Website Optimization Pre-Check Tool
Demonstrates programmatic usage of the analyzer
"""

from website_analyzer import WebsiteAnalyzer
from rich.console import Console

console = Console()

def example_analysis():
    """Example analysis with sample URLs"""
    
    # Sample URLs to analyze
    urls = [
        "https://www.google.com",
        "https://www.github.com",
        "https://www.stackoverflow.com",
        "https://www.wikipedia.org"
    ]
    
    console.print("[bold blue]Website Optimization Pre-Check Tool - Example[/bold blue]")
    console.print(f"Analyzing {len(urls)} URLs...\n")
    
    # Create analyzer
    analyzer = WebsiteAnalyzer(urls)
    
    # Run analysis
    results = analyzer.analyze_all_urls()
    
    # Display results
    console.print("\n[bold green]Analysis Results:[/bold green]")
    
    for url, url_results in results.items():
        console.print(f"\n[cyan]URL:[/cyan] {url}")
        
        summary = url_results.get('summary', {})
        
        if 'desktop_score' in summary and summary['desktop_score'] is not None:
            console.print(f"  Desktop Score: {summary['desktop_score']}")
        
        if 'mobile_score' in summary and summary['mobile_score'] is not None:
            console.print(f"  Mobile Score: {summary['mobile_score']}")
        
        if 'average_score' in summary and summary['average_score'] is not None:
            console.print(f"  Average Score: {summary['average_score']:.1f}")
        
        console.print(f"  Files Generated: {summary.get('files_generated', 0)}")
        console.print(f"  Errors: {summary.get('errors_count', 0)}")
    
    # Show output directory
    output_dir = analyzer.get_output_directory()
    console.print(f"\n[bold green]Output Directory:[/bold green] {output_dir}")
    
    return results

def example_single_url():
    """Example analysis of a single URL"""
    
    url = "https://www.example.com"
    
    console.print(f"[bold blue]Single URL Analysis:[/bold blue] {url}")
    
    # Create analyzer with single URL
    analyzer = WebsiteAnalyzer([url])
    
    # Run analysis
    results = analyzer.analyze_all_urls()
    
    # Get detailed results
    url_results = results.get(url, {})
    
    console.print("\n[bold]Detailed Results:[/bold]")
    
    # Desktop results
    desktop_results = url_results.get('desktop', {})
    console.print("\n[cyan]Desktop Analysis:[/cyan]")
    console.print(f"  Video: {desktop_results.get('video_path', 'N/A')}")
    console.print(f"  Screenshot: {desktop_results.get('screenshot_path', 'N/A')}")
    
    # Mobile results
    mobile_results = url_results.get('mobile', {})
    console.print("\n[cyan]Mobile Analysis:[/cyan]")
    console.print(f"  Video: {mobile_results.get('video_path', 'N/A')}")
    console.print(f"  Screenshot: {mobile_results.get('screenshot_path', 'N/A')}")
    
    return results

def example_custom_config():
    """Example with custom configuration"""
    
    from config import BROWSER_CONFIG, VIDEO_CONFIG
    
    # Modify configuration
    BROWSER_CONFIG['headless'] = True  # Run in headless mode
    VIDEO_CONFIG['duration'] = 15  # Shorter video duration
    
    urls = ["https://www.google.com"]
    
    console.print("[bold blue]Custom Configuration Example[/bold blue]")
    console.print("Running in headless mode with 15-second videos...")
    
    analyzer = WebsiteAnalyzer(urls)
    results = analyzer.analyze_all_urls()
    
    return results

if __name__ == "__main__":
    try:
        # Run example analysis
        example_analysis()
        
        # Uncomment to run other examples:
        # example_single_url()
        # example_custom_config()
        
    except Exception as e:
        console.print(f"[red]Error in example: {str(e)}[/red]") 