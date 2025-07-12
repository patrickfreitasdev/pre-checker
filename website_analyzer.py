"""
Website Analyzer - Main orchestrator for Website Optimization Pre-Check Tool
Coordinates video recording, screenshots, and PageSpeed analysis
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

from browser_manager import BrowserManager
from video_recorder import BrowserVideoRecorder, ScreenRecorder
from pagespeed_analyzer import PageSpeedAPI, SimplePerformanceAnalyzer
from config import (
    VIDEO_CONFIG, SCREENSHOT_CONFIG, 
    get_output_directory, create_directory_structure,
    sanitize_filename, OUTPUT_CONFIG
)

class WebsiteAnalyzer:
    def __init__(self, urls: List[str], modules: List[str] = None):
        """
        Initialize website analyzer
        
        Args:
            urls (List[str]): List of URLs to analyze
            modules (List[str]): List of modules to run ('score', 'screenshot', 'record')
        """
        self.urls = urls
        self.modules = modules or ['score', 'screenshot', 'record']  # Default to all modules
        self.output_dir = get_output_directory()
        self.results = {}
        # Create output directory structure BEFORE setting up logging
        create_directory_structure(self.output_dir)
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.output_dir, 'analysis.log')),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def analyze_all_urls(self):
        """
        Analyze all URLs with comprehensive testing
        
        Returns:
            dict: Complete analysis results
        """
        self.logger.info(f"Starting analysis of {len(self.urls)} URLs")
        
        for i, url in enumerate(self.urls, 1):
            self.logger.info(f"Processing URL {i}/{len(self.urls)}: {url}")
            
            try:
                url_results = self._analyze_single_url(url)
                self.results[url] = url_results
                
                self.logger.info(f"Completed analysis for {url}")
                
            except Exception as e:
                self.logger.error(f"Error analyzing {url}: {str(e)}")
                self.results[url] = {'error': str(e)}
        
        # Generate summary report
        self._generate_summary_report()
        
        # Generate error log summary
        self._generate_error_log_summary()
        
        self.logger.info("Analysis completed for all URLs")
        return self.results
    
    def _analyze_single_url(self, url: str) -> Dict[str, Any]:
        """
        Analyze a single URL with all tests
        
        Args:
            url (str): URL to analyze
            
        Returns:
            dict: Analysis results for the URL
        """
        url_results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'desktop': {},
            'mobile': {},
            'summary': {}
        }
        
        # Analyze for both desktop and mobile
        for viewport in ['desktop', 'mobile']:
            self.logger.info(f"Analyzing {url} for {viewport} viewport")
            
            viewport_results = self._analyze_viewport(url, viewport)
            url_results[viewport] = viewport_results
        
        # Calculate summary metrics
        url_results['summary'] = self._calculate_summary(url_results)
        
        return url_results
    
    def _analyze_viewport(self, url: str, viewport: str) -> Dict[str, Any]:
        """
        Analyze URL for specific viewport (desktop/mobile)
        
        Args:
            url (str): URL to analyze
            viewport (str): 'desktop' or 'mobile'
            
        Returns:
            dict: Viewport-specific results
        """
        viewport_results = {
            'video_path': None,
            'screenshot_path': None,
            'pagespeed_results': {},
            'page_info': {},
            'errors': []
        }
        
        try:
            # Setup browser for this viewport
            with BrowserManager(viewport=viewport) as browser:
                
                # 1. Record video of page navigation (if 'record' module is enabled)
                if 'record' in self.modules:
                    video_path = self._record_page_navigation(browser, url, viewport)
                    viewport_results['video_path'] = video_path
                
                # 2. Take full page screenshot with error capture (if 'screenshot' module is enabled)
                if 'screenshot' in self.modules:
                    screenshot_results = self._take_page_screenshot(browser, url, viewport)
                    viewport_results['screenshot_path'] = screenshot_results['page_screenshot']
                    viewport_results['error_log_path'] = screenshot_results['error_log']
                    viewport_results['error_count'] = screenshot_results['error_count']
                
                # 3. Get page information
                viewport_results['page_info'] = browser.get_page_info()
                
                # 4. Analyze with PageSpeed Insights (if 'score' module is enabled)
                if 'score' in self.modules:
                    pagespeed_results = self._analyze_pagespeed_with_fallback(browser, url)
                    viewport_results['pagespeed_results'] = pagespeed_results
                    
                    # 5. Save PageSpeed results to files
                    pagespeed_files = self._save_pagespeed_results(url, viewport, pagespeed_results)
                    viewport_results['pagespeed_files'] = pagespeed_files
                
        except Exception as e:
            error_msg = f"Error in {viewport} analysis: {str(e)}"
            self.logger.error(error_msg)
            viewport_results['errors'].append(error_msg)
        
        return viewport_results
    
    def _analyze_pagespeed_with_fallback(self, browser: BrowserManager, url: str) -> Dict[str, Any]:
        """
        Analyze PageSpeed with fallback to simple analyzer if API fails
        
        Args:
            browser: BrowserManager instance
            url (str): URL to analyze
            
        Returns:
            dict: PageSpeed analysis results
        """
        try:
            # Try PageSpeed API first
            self.logger.info(f"Attempting PageSpeed API analysis for {url}")
            pagespeed_analyzer = PageSpeedAPI()
            results = pagespeed_analyzer.analyze_all_strategies(url)
            
            # Check if API analysis failed
            api_failed = False
            for strategy, result in results.items():
                if 'error' in result and '429' in str(result['error']):
                    api_failed = True
                    break
            
            if api_failed:
                self.logger.warning(f"PageSpeed API rate limit reached for {url}, using fallback analyzer")
                # Use simple performance analyzer as fallback
                simple_analyzer = SimplePerformanceAnalyzer(browser)
                results = simple_analyzer.analyze_all_strategies(url)
                # Mark these as fallback results
                for strategy in results:
                    if 'error' not in results[strategy]:
                        results[strategy]['fallback'] = True
                        results[strategy]['note'] = 'Using fallback analyzer due to API rate limit'
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in PageSpeed analysis for {url}: {str(e)}")
            # Use simple analyzer as fallback
            try:
                self.logger.info(f"Using fallback analyzer for {url}")
                simple_analyzer = SimplePerformanceAnalyzer(browser)
                results = simple_analyzer.analyze_all_strategies(url)
                # Mark these as fallback results
                for strategy in results:
                    if 'error' not in results[strategy]:
                        results[strategy]['fallback'] = True
                        results[strategy]['note'] = 'Using fallback analyzer due to API error'
                return results
            except Exception as fallback_error:
                self.logger.error(f"Fallback analyzer also failed for {url}: {str(fallback_error)}")
                return {'error': f'Both API and fallback analysis failed: {str(e)}'}
    
    def _save_pagespeed_results(self, url: str, viewport: str, pagespeed_results: Dict[str, Any]) -> Dict[str, str]:
        """
        Save PageSpeed results to files
        
        Args:
            url (str): URL analyzed
            viewport (str): Viewport type
            pagespeed_results (dict): PageSpeed analysis results
            
        Returns:
            dict: Paths to saved files
        """
        import json
        from datetime import datetime
        
        saved_files = {}
        
        try:
            # Create PageSpeed directory for this viewport
            pagespeed_dir = os.path.join(self.output_dir, OUTPUT_CONFIG['subdirs']['pagespeed'], viewport)
            os.makedirs(pagespeed_dir, exist_ok=True)
            
            # Generate base filename
            base_filename = sanitize_filename(url, viewport)
            
            # Save detailed JSON results
            json_filename = f"{base_filename}_pagespeed_results.json"
            json_path = os.path.join(pagespeed_dir, json_filename)
            
            with open(json_path, 'w') as f:
                json.dump(pagespeed_results, f, indent=2, default=str)
            
            saved_files['json_results'] = json_path
            self.logger.info(f"PageSpeed JSON results saved: {json_path}")
            
            # Generate and save summary report
            summary_filename = f"{base_filename}_pagespeed_summary.txt"
            summary_path = os.path.join(pagespeed_dir, summary_filename)
            
            with open(summary_path, 'w') as f:
                f.write(f"PageSpeed Analysis Summary\n")
                f.write(f"=" * 40 + "\n\n")
                f.write(f"URL: {url}\n")
                f.write(f"Viewport: {viewport}\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for strategy, result in pagespeed_results.items():
                    f.write(f"Strategy: {strategy.upper()}\n")
                    f.write(f"-" * 20 + "\n")
                    
                    if 'error' in result:
                        f.write(f"Error: {result['error']}\n")
                    else:
                        f.write(f"Score: {result.get('score', 'N/A')}/100\n")
                        
                        if 'fallback' in result:
                            f.write(f"Note: {result.get('note', 'Using fallback analyzer')}\n")
                        
                        if 'metrics' in result:
                            metrics = result['metrics']
                            f.write(f"Load Time: {metrics.get('load_time', 'N/A')}ms\n")
                            f.write(f"DOM Ready Time: {metrics.get('dom_ready_time', 'N/A')}ms\n")
                            f.write(f"First Paint: {metrics.get('first_paint', 'N/A')}ms\n")
                            f.write(f"Page Size: {metrics.get('page_size', 'N/A')} pixels\n")
                        
                        if 'timestamp' in result:
                            f.write(f"Timestamp: {datetime.fromtimestamp(result['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
                    f.write("\n")
            
            saved_files['summary_report'] = summary_path
            self.logger.info(f"PageSpeed summary report saved: {summary_path}")
            
            # Generate visual score chart (simple text-based)
            chart_filename = f"{base_filename}_pagespeed_chart.txt"
            chart_path = os.path.join(pagespeed_dir, chart_filename)
            
            with open(chart_path, 'w') as f:
                f.write(f"PageSpeed Performance Chart\n")
                f.write(f"=" * 40 + "\n\n")
                
                for strategy, result in pagespeed_results.items():
                    if 'error' not in result and 'score' in result:
                        score = result['score']
                        f.write(f"{strategy.upper()} Performance: ")
                        
                        # Create visual score bar
                        filled_bars = int(score / 10)
                        empty_bars = 10 - filled_bars
                        bar = "█" * filled_bars + "░" * empty_bars
                        
                        f.write(f"{bar} {score}/100\n")
                        
                        if score >= 90:
                            f.write("Status: Excellent\n")
                        elif score >= 70:
                            f.write("Status: Good\n")
                        elif score >= 50:
                            f.write("Status: Needs Improvement\n")
                        else:
                            f.write("Status: Poor\n")
                        
                        f.write("\n")
            
            saved_files['performance_chart'] = chart_path
            self.logger.info(f"PageSpeed performance chart saved: {chart_path}")
            
            # Generate visual score screenshot
            score_screenshot_path = self._generate_score_screenshot(url, viewport, pagespeed_results)
            if score_screenshot_path:
                saved_files['score_screenshot'] = score_screenshot_path
                self.logger.info(f"PageSpeed score screenshot saved: {score_screenshot_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving PageSpeed results for {url} ({viewport}): {str(e)}")
        
        return saved_files
    
    def _generate_score_screenshot(self, url: str, viewport: str, pagespeed_results: Dict[str, Any]) -> str:
        """
        Generate a visual screenshot of PageSpeed scores
        
        Args:
            url (str): URL analyzed
            viewport (str): Viewport type
            pagespeed_results (dict): PageSpeed analysis results
            
        Returns:
            str: Path to score screenshot file
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            from matplotlib.patches import FancyBboxPatch
            import numpy as np
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('#f8f9fa')
            ax.set_facecolor('#f8f9fa')
            
            # Set title
            title = f"PageSpeed Analysis - {viewport.upper()}"
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # Extract scores
            scores = []
            labels = []
            colors = []
            
            for strategy, result in pagespeed_results.items():
                if 'error' not in result and 'score' in result:
                    score = result['score']
                    scores.append(score)
                    labels.append(strategy.upper())
                    
                    # Color based on score
                    if score >= 90:
                        colors.append('#28a745')  # Green
                    elif score >= 70:
                        colors.append('#ffc107')  # Yellow
                    elif score >= 50:
                        colors.append('#fd7e14')  # Orange
                    else:
                        colors.append('#dc3545')  # Red
            
            if not scores:
                return None
            
            # Create horizontal bar chart
            y_pos = np.arange(len(scores))
            bars = ax.barh(y_pos, scores, color=colors, height=0.6, edgecolor='white', linewidth=2)
            
            # Add score values on bars
            for i, (bar, score) in enumerate(zip(bars, scores)):
                width = bar.get_width()
                ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                       f'{score}/100', ha='left', va='center', fontweight='bold', fontsize=12)
            
            # Customize chart
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=12, fontweight='bold')
            ax.set_xlim(0, 100)
            ax.set_xlabel('Performance Score', fontsize=12, fontweight='bold')
            
            # Add grid
            ax.grid(True, axis='x', alpha=0.3)
            ax.set_axisbelow(True)
            
            # Add score zones
            zones = [(0, 49, '#dc3545', 'Poor'), 
                    (50, 69, '#fd7e14', 'Needs Improvement'),
                    (70, 89, '#ffc107', 'Good'),
                    (90, 100, '#28a745', 'Excellent')]
            
            for start, end, color, label in zones:
                ax.axvspan(start, end, alpha=0.1, color=color)
                ax.text((start + end) / 2, -0.5, label, ha='center', va='top', 
                       fontsize=10, fontweight='bold', color=color)
            
            # Add URL info
            ax.text(0.02, 0.98, f'URL: {url}', transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top', 
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
            
            # Add timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ax.text(0.98, 0.02, f'Generated: {timestamp}', transform=ax.transAxes, 
                   fontsize=8, horizontalalignment='right', verticalalignment='bottom',
                   style='italic', alpha=0.7)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save screenshot
            screenshot_filename = f"{sanitize_filename(url, viewport)}_pagespeed_score.png"
            pagespeed_dir = os.path.join(self.output_dir, OUTPUT_CONFIG['subdirs']['pagespeed'], viewport)
            screenshot_path = os.path.join(pagespeed_dir, screenshot_filename)
            plt.savefig(screenshot_path, dpi=150, bbox_inches='tight', facecolor='#f8f9fa')
            plt.close()
            
            return screenshot_path
            
        except ImportError:
            self.logger.warning("matplotlib not available. Skipping score screenshot generation.")
            return None
        except Exception as e:
            self.logger.error(f"Error generating score screenshot: {str(e)}")
            return None
    
    def _record_page_navigation(self, browser: BrowserManager, url: str, viewport: str) -> str:
        """
        Record video of page navigation
        
        Args:
            browser: BrowserManager instance
            url (str): URL to navigate to
            viewport (str): Viewport type
            
        Returns:
            str: Path to recorded video file
        """
        try:
            # Generate video filename
            filename = sanitize_filename(url, viewport)
            video_filename = f"{filename}.{VIDEO_CONFIG['output_format']}"
            video_dir = os.path.join(self.output_dir, OUTPUT_CONFIG['subdirs']['videos'], viewport)
            # Ensure the video directory exists
            os.makedirs(video_dir, exist_ok=True)
            video_path = os.path.join(video_dir, video_filename)
            
            # Navigate to URL
            if not browser.navigate_to_url(url):
                raise Exception("Failed to navigate to URL")
            
            # Start video recording with extended duration to account for lazy loading detection
            extended_duration = VIDEO_CONFIG['duration'] + 15  # Add 15 seconds for lazy loading detection
            recorder = BrowserVideoRecorder(
                browser_driver=browser.driver,
                output_path=video_path,
                fps=VIDEO_CONFIG['fps'],
                duration=extended_duration
            )
            
            if recorder.start_recording():
                self.logger.info(f"Started video recording for {url} ({viewport})")
                
                # Perform page navigation (scroll from top to bottom)
                browser.scroll_page(
                    duration=VIDEO_CONFIG['duration'],
                    steps=VIDEO_CONFIG['scroll_steps']
                )
                
                # Wait a bit more to ensure we capture the final scroll to bottom
                time.sleep(2)
                
                # Stop recording
                recorder.stop_recording()
                self.logger.info(f"Video recording completed: {video_path}")
                
                return video_path
            else:
                raise Exception("Failed to start video recording")
                
        except Exception as e:
            self.logger.error(f"Error recording video for {url} ({viewport}): {str(e)}")
            return None
    
    def _take_page_screenshot(self, browser: BrowserManager, url: str, viewport: str) -> Dict[str, str]:
        """
        Take full page screenshot with error capture and console logging
        
        Args:
            browser: BrowserManager instance
            url (str): URL being analyzed
            viewport (str): Viewport type
            
        Returns:
            dict: Paths to screenshot files and error information
        """
        try:
            # Generate screenshot filenames
            filename = sanitize_filename(url, viewport)
            page_screenshot_filename = f"{filename}.png"
            error_log_filename = f"{filename}_console_errors.json"
            
            screenshot_dir = os.path.join(self.output_dir, OUTPUT_CONFIG['subdirs']['screenshots'], viewport)
            # Ensure the screenshot directory exists
            os.makedirs(screenshot_dir, exist_ok=True)
            
            page_screenshot_path = os.path.join(screenshot_dir, page_screenshot_filename)
            error_log_path = os.path.join(screenshot_dir, error_log_filename)
            
            # Navigate to URL if not already navigated
            if not browser.navigate_to_url(url):
                raise Exception("Failed to navigate to URL")
            
            # Wait for page to fully load
            time.sleep(SCREENSHOT_CONFIG['delay'])
            
            # First, scroll through the page to trigger any lazy loading and capture errors
            self.logger.info(f"Starting error capture scroll for {url} ({viewport})")
            error_info = browser.scroll_and_capture_errors(duration=15)
            
            # Log error capture results
            if error_info['capture_status'] == 'success':
                if error_info['error_summary']['has_errors']:
                    self.logger.info(f"Error capture completed for {url} ({viewport}): Found {error_info['total_errors']} errors")
                    if error_info['error_summary']['error_types_found']:
                        self.logger.info(f"Error types found: {', '.join(error_info['error_summary']['error_types_found'])}")
                else:
                    self.logger.info(f"Error capture completed for {url} ({viewport}): No errors found - page appears to be error-free")
            else:
                self.logger.warning(f"Error capture failed for {url} ({viewport}): {error_info.get('capture_error', 'Unknown error')}")
            
            # Save error information to JSON file
            import json
            with open(error_log_path, 'w') as f:
                json.dump(error_info, f, indent=2)
            
            # Take page screenshot after scrolling
            if browser.take_screenshot(page_screenshot_path, full_page=SCREENSHOT_CONFIG['full_page']):
                self.logger.info(f"Page screenshot saved: {page_screenshot_path}")
            else:
                raise Exception("Failed to take page screenshot")
            
            return {
                'page_screenshot': page_screenshot_path,
                'error_log': error_log_path,
                'error_count': error_info['total_errors']
            }
                
        except Exception as e:
            self.logger.error(f"Error taking screenshots for {url} ({viewport}): {str(e)}")
            return {
                'page_screenshot': None,
                'error_log': None,
                'error_count': 0
            }
    
    def _calculate_summary(self, url_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate summary metrics for URL results
        
        Args:
            url_results (dict): Complete results for a URL
            
        Returns:
            dict: Summary metrics
        """
        summary = {
            'desktop_score': None,
            'mobile_score': None,
            'average_score': None,
            'files_generated': 0,
            'errors_count': 0
        }
        
        # Count files and errors
        for viewport in ['desktop', 'mobile']:
            viewport_data = url_results.get(viewport, {})
            
            # Count files
            if viewport_data.get('video_path'):
                summary['files_generated'] += 1
            if viewport_data.get('screenshot_path'):
                summary['files_generated'] += 1
            if viewport_data.get('error_log_path'):
                summary['files_generated'] += 1
            
            # Count PageSpeed files
            pagespeed_files = viewport_data.get('pagespeed_files', {})
            summary['files_generated'] += len(pagespeed_files)
            
            # Count errors
            summary['errors_count'] += len(viewport_data.get('errors', []))
            
            # Extract PageSpeed scores
            pagespeed_results = viewport_data.get('pagespeed_results', {})
            for strategy, result in pagespeed_results.items():
                if strategy == viewport and 'score' in result:
                    summary[f'{viewport}_score'] = result['score']
        
        # Calculate average score
        scores = [s for s in [summary['desktop_score'], summary['mobile_score']] if s is not None]
        if scores:
            summary['average_score'] = sum(scores) / len(scores)
        
        return summary
    
    def _generate_summary_report(self):
        """Generate a summary report of all analysis results"""
        try:
            report_path = os.path.join(self.output_dir, 'summary_report.txt')
            
            with open(report_path, 'w') as f:
                f.write("Website Optimization Pre-Check Summary Report\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URLs Analyzed: {len(self.urls)}\n\n")
                
                # Overall statistics
                total_files = 0
                total_errors = 0
                scores = []
                
                for url, results in self.results.items():
                    f.write(f"URL: {url}\n")
                    f.write("-" * 30 + "\n")
                    
                    summary = results.get('summary', {})
                    total_files += summary.get('files_generated', 0)
                    total_errors += summary.get('errors_count', 0)
                    
                    if summary.get('desktop_score') is not None:
                        scores.append(summary['desktop_score'])
                        f.write(f"Desktop Score: {summary['desktop_score']}\n")
                    
                    if summary.get('mobile_score') is not None:
                        scores.append(summary['mobile_score'])
                        f.write(f"Mobile Score: {summary['mobile_score']}\n")
                    
                    if summary.get('average_score') is not None:
                        f.write(f"Average Score: {summary['average_score']:.1f}\n")
                    
                    f.write(f"Files Generated: {summary.get('files_generated', 0)}\n")
                    f.write(f"Errors: {summary.get('errors_count', 0)}\n")
                    
                    # Add console error information
                    desktop_errors = results.get('desktop', {}).get('error_count', 0)
                    mobile_errors = results.get('mobile', {}).get('error_count', 0)
                    if desktop_errors > 0 or mobile_errors > 0:
                        f.write(f"Console Errors - Desktop: {desktop_errors}, Mobile: {mobile_errors}\n")
                    else:
                        f.write("Console Errors - None found (clean)\n")
                    
                    f.write("\n")
                
                # Overall summary
                f.write("Overall Summary\n")
                f.write("-" * 30 + "\n")
                f.write(f"Total Files Generated: {total_files}\n")
                f.write(f"Total Errors: {total_errors}\n")
                
                if scores:
                    f.write(f"Average Score Across All Tests: {sum(scores) / len(scores):.1f}\n")
                    f.write(f"Best Score: {max(scores)}\n")
                    f.write(f"Worst Score: {min(scores)}\n")
                
                # Calculate and display averages by device type
                desktop_scores = []
                mobile_scores = []
                
                for url, results in self.results.items():
                    summary = results.get('summary', {})
                    if summary.get('desktop_score') is not None:
                        desktop_scores.append(summary['desktop_score'])
                    if summary.get('mobile_score') is not None:
                        mobile_scores.append(summary['mobile_score'])
                
                if desktop_scores:
                    f.write(f"Average Desktop Score: {sum(desktop_scores) / len(desktop_scores):.1f}\n")
                if mobile_scores:
                    f.write(f"Average Mobile Score: {sum(mobile_scores) / len(mobile_scores):.1f}\n")
                
                # --- Score Breakdown Table ---
                f.write("\nScore Breakdown Table\n")
                f.write("=" * 40 + "\n")
                f.write("         |   Score (per URL)                | Avg\n")
                f.write("---------|-----------------------------------|------\n")
                f.write("Mobile   | " + " ".join(str(s) for s in mobile_scores) + f" | {sum(mobile_scores)} | {sum(mobile_scores)/len(mobile_scores) if mobile_scores else 0:.1f}\n")
                f.write("Desktop  | " + " ".join(str(s) for s in desktop_scores) + f" | {sum(desktop_scores)} | {sum(desktop_scores)/len(desktop_scores) if desktop_scores else 0:.1f}\n")
                
                f.write(f"\nOutput Directory: {self.output_dir}\n")
            
            self.logger.info(f"Summary report generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {str(e)}")
    
    def _generate_error_log_summary(self):
        """Generate a detailed error log summary report"""
        try:
            report_path = os.path.join(self.output_dir, 'error_log_summary.txt')
            self.logger.info(f"Generating error log summary at: {report_path}")
            
            with open(report_path, 'w') as f:
                f.write("Website Error Capture Summary Report\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URLs Analyzed: {len(self.urls)}\n\n")
                
                # Overall error statistics
                total_urls_with_errors = 0
                total_errors_found = 0
                error_types_summary = {
                    'console_errors': 0,
                    'page_errors': 0,
                    'browser_logs': 0,
                    'scroll_errors': 0
                }
                
                for url, results in self.results.items():
                    self.logger.info(f"Processing error summary for URL: {url}")
                    f.write(f"URL: {url}\n")
                    f.write("-" * 50 + "\n")
                    
                    for viewport in ['desktop', 'mobile']:
                        viewport_data = results.get(viewport, {})
                        error_count = viewport_data.get('error_count', 0)
                        error_log_path = viewport_data.get('error_log_path')
                        
                        f.write(f"\n{viewport.upper()} VIEWPORT:\n")
                        
                        if error_log_path and os.path.exists(error_log_path):
                            self.logger.info(f"Reading error log: {error_log_path}")
                            try:
                                import json
                                with open(error_log_path, 'r') as error_file:
                                    error_data = json.load(error_file)
                                
                                # Check capture status
                                capture_status = error_data.get('capture_status', 'unknown')
                                self.logger.info(f"Capture status for {url} ({viewport}): {capture_status}")
                                if capture_status == 'success':
                                    has_errors = error_data.get('error_summary', {}).get('has_errors', False)
                                    total_errors = error_data.get('total_errors', 0)
                                    self.logger.info(f"Error summary for {url} ({viewport}): has_errors={has_errors}, total_errors={total_errors}")
                                    
                                    if has_errors:
                                        total_urls_with_errors += 1
                                        total_errors_found += total_errors
                                        
                                        f.write(f"  Status: ERRORS FOUND ({error_data.get('total_errors', 0)} total)\n")
                                        
                                        # Error type breakdown
                                        error_types = error_data.get('error_summary', {}).get('error_types_found', [])
                                        if error_types:
                                            f.write(f"  Error Types: {', '.join(error_types)}\n")
                                        
                                        # Detailed error counts - also check scroll errors
                                        console_count = len(error_data.get('console_errors', []))
                                        page_count = len(error_data.get('page_errors', []))
                                        browser_count = len(error_data.get('browser_logs', []))
                                        scroll_count = len(error_data.get('scroll_errors', []))
                                        
                                        # Aggregate errors from scroll positions
                                        scroll_console_errors = []
                                        scroll_page_errors = []
                                        scroll_browser_logs = []
                                        
                                        for scroll_error in error_data.get('scroll_errors', []):
                                            scroll_errors_data = scroll_error.get('errors', {})
                                            scroll_console_errors.extend(scroll_errors_data.get('console_errors', []))
                                            scroll_page_errors.extend(scroll_errors_data.get('page_errors', []))
                                            scroll_browser_logs.extend(scroll_errors_data.get('browser_logs', []))
                                        
                                        # Add scroll errors to totals
                                        console_count += len(scroll_console_errors)
                                        page_count += len(scroll_page_errors)
                                        browser_count += len(scroll_browser_logs)
                                        
                                        if console_count > 0:
                                            f.write(f"  Console Errors: {console_count}\n")
                                            error_types_summary['console_errors'] += console_count
                                        if page_count > 0:
                                            f.write(f"  Page Errors: {page_count}\n")
                                            error_types_summary['page_errors'] += page_count
                                        if browser_count > 0:
                                            f.write(f"  Browser Logs: {browser_count}\n")
                                            error_types_summary['browser_logs'] += browser_count
                                        if scroll_count > 0:
                                            f.write(f"  Scroll Positions with Errors: {scroll_count}\n")
                                            error_types_summary['scroll_errors'] += scroll_count
                                        
                                        # Show some example errors (including from scroll positions)
                                        all_console_errors = error_data.get('console_errors', []) + scroll_console_errors
                                        if all_console_errors:
                                            f.write(f"  Sample Console Errors:\n")
                                            for i, error in enumerate(all_console_errors[:3]):  # Show first 3
                                                message = error.get('message', 'Unknown error')
                                                f.write(f"    {i+1}. {message[:100]}{'...' if len(message) > 100 else ''}\n")
                                        
                                        all_browser_logs = error_data.get('browser_logs', []) + scroll_browser_logs
                                        if all_browser_logs:
                                            f.write(f"  Sample Browser Logs:\n")
                                            for i, log in enumerate(all_browser_logs[:3]):  # Show first 3
                                                message = log.get('message', 'Unknown log')
                                                level = log.get('level', 'UNKNOWN')
                                                f.write(f"    {i+1}. [{level}] {message[:100]}{'...' if len(message) > 100 else ''}\n")
                                        
                                    else:
                                        f.write(f"  Status: CLEAN (No errors found)\n")
                                else:
                                    f.write(f"  Status: CAPTURE FAILED\n")
                                    if 'capture_error' in error_data:
                                        f.write(f"  Error: {error_data['capture_error']}\n")
                                
                                # Timestamp
                                capture_time = error_data.get('capture_timestamp')
                                if capture_time:
                                    dt = datetime.fromtimestamp(capture_time)
                                    f.write(f"  Captured: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
                                
                            except Exception as e:
                                self.logger.error(f"Error reading error log {error_log_path}: {str(e)}")
                                f.write(f"  Status: ERROR READING LOG ({str(e)})\n")
                        else:
                            self.logger.warning(f"No error log found at: {error_log_path}")
                            f.write(f"  Status: NO ERROR LOG FOUND\n")
                    
                    f.write("\n")
                
                # Overall summary
                f.write("OVERALL ERROR SUMMARY\n")
                f.write("-" * 30 + "\n")
                f.write(f"URLs with Errors: {total_urls_with_errors}/{len(self.urls)}\n")
                f.write(f"Total Errors Found: {total_errors_found}\n")
                f.write(f"Clean URLs: {len(self.urls) - total_urls_with_errors}\n\n")
                
                if total_errors_found > 0:
                    f.write("Error Type Breakdown:\n")
                    for error_type, count in error_types_summary.items():
                        if count > 0:
                            f.write(f"  {error_type.replace('_', ' ').title()}: {count}\n")
                
                # Recommendations
                f.write("\nRECOMMENDATIONS:\n")
                f.write("-" * 20 + "\n")
                if total_urls_with_errors == 0:
                    f.write("✓ All URLs appear to be error-free\n")
                    f.write("✓ No immediate action required\n")
                else:
                    f.write(f"⚠ {total_urls_with_errors} URL(s) have errors that should be investigated\n")
                    if error_types_summary['console_errors'] > 0:
                        f.write("  - Review JavaScript console errors\n")
                    if error_types_summary['browser_logs'] > 0:
                        f.write("  - Check browser-level errors and warnings\n")
                    if error_types_summary['page_errors'] > 0:
                        f.write("  - Review page error elements and user-facing error messages\n")
                    if error_types_summary['scroll_errors'] > 0:
                        f.write("  - Investigate errors that appear during page scrolling\n")
                
                f.write(f"\nDetailed error logs available in: {self.output_dir}/screenshots/\n")
            
            self.logger.info(f"Error log summary generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating error log summary: {str(e)}")
    
    def get_results(self) -> Dict[str, Any]:
        """Get analysis results"""
        return self.results
    
    def get_output_directory(self) -> str:
        """Get output directory path"""
        return self.output_dir 