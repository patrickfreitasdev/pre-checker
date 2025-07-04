"""
PageSpeed Analyzer for Website Optimization Pre-Check Tool
Integrates with Google PageSpeed Insights for performance analysis
"""

import time
import requests
from urllib.parse import urlencode, quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import PAGESPEED_CONFIG
import logging

class PageSpeedAnalyzer:
    def __init__(self, browser_manager):
        """
        Initialize PageSpeed analyzer
        
        Args:
            browser_manager: BrowserManager instance for web automation
        """
        self.browser_manager = browser_manager
        self.logger = logging.getLogger(__name__)
        self.base_url = PAGESPEED_CONFIG['base_url']
        
    def analyze_url(self, url, strategy='mobile'):
        """
        Analyze a URL using PageSpeed Insights
        
        Args:
            url (str): URL to analyze
            strategy (str): 'mobile' or 'desktop'
            
        Returns:
            dict: Analysis results including score and screenshot path
        """
        try:
            self.logger.info(f"Starting PageSpeed analysis for {url} ({strategy})")
            
            # Navigate to PageSpeed Insights
            pagespeed_url = self._build_pagespeed_url(url, strategy)
            
            if not self.browser_manager.navigate_to_url(pagespeed_url):
                return {'error': 'Failed to navigate to PageSpeed Insights'}
            
            # Wait for results to load
            if not self._wait_for_results():
                return {'error': 'PageSpeed results did not load in time'}
            
            # Get performance score
            score = self._extract_performance_score()
            
            # Take screenshot of results
            screenshot_path = self._take_results_screenshot(url, strategy)
            
            # Get detailed metrics
            metrics = self._extract_metrics()
            
            results = {
                'url': url,
                'strategy': strategy,
                'score': score,
                'screenshot_path': screenshot_path,
                'metrics': metrics,
                'timestamp': time.time()
            }
            
            self.logger.info(f"PageSpeed analysis completed for {url} ({strategy}): Score {score}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing {url} with strategy {strategy}: {str(e)}")
            return {'error': str(e)}
    
    def _build_pagespeed_url(self, url, strategy):
        """
        Build PageSpeed Insights URL
        
        Args:
            url (str): URL to analyze
            strategy (str): 'mobile' or 'desktop'
            
        Returns:
            str: Complete PageSpeed Insights URL
        """
        # PageSpeed Insights URL format
        base_url = self.base_url.rstrip('/')
        encoded_url = quote(url, safe='')
        
        # Build the URL with parameters
        params = {
            'url': url,
            'tab': strategy
        }
        
        pagespeed_url = f"{base_url}/?{urlencode(params)}"
        return pagespeed_url
    
    def _wait_for_results(self, timeout=30):
        """
        Wait for PageSpeed results to load
        
        Args:
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if results loaded, False otherwise
        """
        try:
            # Wait for the performance score to appear
            score_selector = '[data-testid="lh-gauge__score"]'
            WebDriverWait(self.browser_manager.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, score_selector))
            )
            
            # Additional wait for metrics to load
            metrics_selector = '[data-testid="lh-metric"]'
            WebDriverWait(self.browser_manager.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, metrics_selector))
            )
            
            self.logger.info("PageSpeed results loaded successfully")
            return True
            
        except TimeoutException:
            self.logger.error("Timeout waiting for PageSpeed results")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for results: {str(e)}")
            return False
    
    def _extract_performance_score(self):
        """
        Extract the performance score from PageSpeed results
        
        Returns:
            int: Performance score (0-100) or None if not found
        """
        try:
            # Try multiple selectors for the performance score
            score_selectors = [
                '[data-testid="lh-gauge__score"]',
                '.lh-gauge__score',
                '.lh-score__value',
                '[data-testid="score"]'
            ]
            
            for selector in score_selectors:
                try:
                    score_element = self.browser_manager.driver.find_element(By.CSS_SELECTOR, selector)
                    score_text = score_element.text.strip()
                    
                    # Extract numeric score
                    if score_text.isdigit():
                        return int(score_text)
                    elif '/' in score_text:
                        # Handle format like "95/100"
                        score = score_text.split('/')[0]
                        if score.isdigit():
                            return int(score)
                except:
                    continue
            
            self.logger.warning("Could not extract performance score")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting performance score: {str(e)}")
            return None
    
    def _extract_metrics(self):
        """
        Extract detailed performance metrics
        
        Returns:
            dict: Dictionary of metrics
        """
        metrics = {}
        
        try:
            # Common PageSpeed metrics
            metric_selectors = {
                'first_contentful_paint': '[data-testid="first-contentful-paint"]',
                'largest_contentful_paint': '[data-testid="largest-contentful-paint"]',
                'first_input_delay': '[data-testid="first-input-delay"]',
                'cumulative_layout_shift': '[data-testid="cumulative-layout-shift"]',
                'speed_index': '[data-testid="speed-index"]'
            }
            
            for metric_name, selector in metric_selectors.items():
                try:
                    element = self.browser_manager.driver.find_element(By.CSS_SELECTOR, selector)
                    value = element.text.strip()
                    metrics[metric_name] = value
                except:
                    metrics[metric_name] = 'N/A'
            
        except Exception as e:
            self.logger.error(f"Error extracting metrics: {str(e)}")
        
        return metrics
    
    def _take_results_screenshot(self, url, strategy):
        """
        Take screenshot of PageSpeed results
        
        Args:
            url (str): Original URL being analyzed
            strategy (str): 'mobile' or 'desktop'
            
        Returns:
            str: Path to saved screenshot
        """
        try:
            import os
            # Generate filename
            from config import sanitize_filename
            filename = sanitize_filename(url, strategy)
            screenshot_filename = f"{filename}_pagespeed_score.png"
            
            # Get screenshot directory
            from config import get_output_directory, OUTPUT_CONFIG
            output_dir = get_output_directory()
            screenshot_dir = os.path.join(output_dir, OUTPUT_CONFIG['subdirs']['pagespeed'], strategy)
            screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
            
            # Take screenshot
            if self.browser_manager.take_screenshot(screenshot_path, full_page=False):
                self.logger.info(f"PageSpeed screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                self.logger.error("Failed to take PageSpeed screenshot")
                return None
                
        except Exception as e:
            self.logger.error(f"Error taking PageSpeed screenshot: {str(e)}")
            return None
    
    def analyze_all_strategies(self, url):
        """
        Analyze URL for both mobile and desktop strategies
        
        Args:
            url (str): URL to analyze
            
        Returns:
            dict: Results for both strategies
        """
        results = {}
        
        for strategy in PAGESPEED_CONFIG['strategies']:
            self.logger.info(f"Analyzing {url} for {strategy} strategy")
            result = self.analyze_url(url, strategy)
            results[strategy] = result
            
            # Wait between analyses
            time.sleep(2)
        
        return results

class PageSpeedAPI:
    """
    Alternative PageSpeed analyzer using the PageSpeed Insights API
    Note: Requires API key for production use
    """
    
    def __init__(self, api_key=None):
        """
        Initialize PageSpeed API analyzer
        
        Args:
            api_key (str): Google PageSpeed Insights API key (optional)
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        self.logger = logging.getLogger(__name__)
    
    def analyze_url(self, url, strategy='mobile'):
        """
        Analyze URL using PageSpeed Insights API
        
        Args:
            url (str): URL to analyze
            strategy (str): 'mobile' or 'desktop'
            
        Returns:
            dict: API response with performance data
        """
        try:
            params = {
                'url': url,
                'strategy': strategy,
                'category': 'performance'
            }
            
            if self.api_key:
                params['key'] = self.api_key
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract key metrics
            lighthouse_result = data.get('lighthouseResult', {})
            categories = lighthouse_result.get('categories', {})
            performance = categories.get('performance', {})
            
            results = {
                'url': url,
                'strategy': strategy,
                'score': performance.get('score', 0) * 100,  # Convert to 0-100 scale
                'metrics': self._extract_api_metrics(lighthouse_result),
                'timestamp': time.time()
            }
            
            self.logger.info(f"API analysis completed for {url} ({strategy}): Score {results['score']}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in API analysis for {url}: {str(e)}")
            return {'error': str(e)}
    
    def _extract_api_metrics(self, lighthouse_result):
        """Extract metrics from API response"""
        metrics = {}
        
        try:
            audits = lighthouse_result.get('audits', {})
            
            # Extract key metrics
            key_metrics = {
                'first_contentful_paint': 'first-contentful-paint',
                'largest_contentful_paint': 'largest-contentful-paint',
                'first_input_delay': 'max-potential-fid',
                'cumulative_layout_shift': 'cumulative-layout-shift',
                'speed_index': 'speed-index'
            }
            
            for metric_name, audit_key in key_metrics.items():
                if audit_key in audits:
                    audit = audits[audit_key]
                    metrics[metric_name] = {
                        'value': audit.get('numericValue'),
                        'display_value': audit.get('displayValue'),
                        'score': audit.get('score')
                    }
            
        except Exception as e:
            self.logger.error(f"Error extracting API metrics: {str(e)}")
        
        return metrics
    
    def analyze_all_strategies(self, url):
        """
        Analyze URL for both mobile and desktop strategies
        
        Args:
            url (str): URL to analyze
        Returns:
            dict: Results for both strategies
        """
        from config import PAGESPEED_CONFIG
        results = {}
        for strategy in PAGESPEED_CONFIG['strategies']:
            self.logger.info(f"Analyzing {url} for {strategy} strategy")
            result = self.analyze_url(url, strategy)
            results[strategy] = result
            time.sleep(2)
        return results 

class SimplePerformanceAnalyzer:
    """
    Simple performance analyzer that provides basic metrics without external APIs
    """
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.logger = logging.getLogger(__name__)
    
    def analyze_url(self, url, strategy='mobile'):
        """
        Analyze URL performance using browser metrics
        
        Args:
            url (str): URL to analyze
            strategy (str): 'mobile' or 'desktop'
            
        Returns:
            dict: Analysis results
        """
        try:
            self.logger.info(f"Starting simple performance analysis for {url} ({strategy})")
            
            # Navigate to URL
            if not self.browser_manager.navigate_to_url(url):
                return {'error': 'Failed to navigate to URL'}
            
            # Wait for page to load
            time.sleep(3)
            
            # Get performance metrics
            metrics = self._get_performance_metrics()
            
            # Calculate a simple performance score
            score = self._calculate_performance_score(metrics)
            
            results = {
                'url': url,
                'strategy': strategy,
                'score': score,
                'metrics': metrics,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Simple performance analysis completed for {url} ({strategy}): Score {score}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in simple performance analysis for {url}: {str(e)}")
            return {'error': str(e)}
    
    def _get_performance_metrics(self):
        """Get basic performance metrics from browser"""
        try:
            # Get navigation timing
            navigation_timing = self.browser_manager.driver.execute_script("""
                var timing = performance.timing;
                return {
                    'domContentLoaded': timing.domContentLoadedEventEnd - timing.navigationStart,
                    'loadComplete': timing.loadEventEnd - timing.navigationStart,
                    'firstPaint': performance.getEntriesByType('paint')[0]?.startTime || 0
                };
            """)
            
            # Get page size info
            page_info = self.browser_manager.get_page_info()
            
            metrics = {
                'load_time': navigation_timing.get('loadComplete', 0),
                'dom_ready_time': navigation_timing.get('domContentLoaded', 0),
                'first_paint': navigation_timing.get('firstPaint', 0),
                'page_size': page_info.get('page_height', 0) * page_info.get('page_width', 0),
                'viewport_size': page_info.get('viewport_height', 0) * page_info.get('viewport_width', 0)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            return {}
    
    def _calculate_performance_score(self, metrics):
        """Calculate a simple performance score based on metrics"""
        try:
            score = 100
            
            # Deduct points for slow load times
            load_time = metrics.get('load_time', 0)
            if load_time > 5000:  # 5 seconds
                score -= 30
            elif load_time > 3000:  # 3 seconds
                score -= 20
            elif load_time > 2000:  # 2 seconds
                score -= 10
            
            # Deduct points for large page size
            page_size = metrics.get('page_size', 0)
            if page_size > 2000000:  # 2M pixels
                score -= 20
            elif page_size > 1000000:  # 1M pixels
                score -= 10
            
            # Ensure score is between 0 and 100
            score = max(0, min(100, score))
            
            return round(score)
            
        except Exception as e:
            self.logger.error(f"Error calculating performance score: {str(e)}")
            return 50  # Default score
    
    def analyze_all_strategies(self, url):
        """
        Analyze URL for both mobile and desktop strategies
        
        Args:
            url (str): URL to analyze
            
        Returns:
            dict: Results for both strategies
        """
        from config import PAGESPEED_CONFIG
        results = {}
        
        for strategy in PAGESPEED_CONFIG['strategies']:
            self.logger.info(f"Analyzing {url} for {strategy} strategy")
            result = self.analyze_url(url, strategy)
            results[strategy] = result
            
            # Wait between analyses
            time.sleep(2)
        
        return results 