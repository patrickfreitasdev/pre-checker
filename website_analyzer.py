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
                
                # 2. Take full page screenshot (if 'screenshot' module is enabled)
                if 'screenshot' in self.modules:
                    screenshot_path = self._take_page_screenshot(browser, url, viewport)
                    viewport_results['screenshot_path'] = screenshot_path
                
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
    
    def _take_page_screenshot(self, browser: BrowserManager, url: str, viewport: str) -> str:
        """
        Take full page screenshot
        
        Args:
            browser: BrowserManager instance
            url (str): URL being analyzed
            viewport (str): Viewport type
            
        Returns:
            str: Path to screenshot file
        """
        try:
            # Generate screenshot filename
            filename = sanitize_filename(url, viewport)
            screenshot_filename = f"{filename}.png"
            screenshot_dir = os.path.join(self.output_dir, OUTPUT_CONFIG['subdirs']['screenshots'], viewport)
            # Ensure the screenshot directory exists
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
            
            # Wait for page to fully load
            time.sleep(SCREENSHOT_CONFIG['delay'])
            
            # Take screenshot
            if browser.take_screenshot(screenshot_path, full_page=SCREENSHOT_CONFIG['full_page']):
                self.logger.info(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                raise Exception("Failed to take screenshot")
                
        except Exception as e:
            self.logger.error(f"Error taking screenshot for {url} ({viewport}): {str(e)}")
            return None
    
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
                    f.write(f"Errors: {summary.get('errors_count', 0)}\n\n")
                
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
                
                f.write(f"\nOutput Directory: {self.output_dir}\n")
            
            self.logger.info(f"Summary report generated: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {str(e)}")
    
    def get_results(self) -> Dict[str, Any]:
        """Get analysis results"""
        return self.results
    
    def get_output_directory(self) -> str:
        """Get output directory path"""
        return self.output_dir 