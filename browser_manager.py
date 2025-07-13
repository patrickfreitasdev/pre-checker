"""
Browser Manager for Website Optimization Pre-Check Tool
Handles Selenium WebDriver setup and management
"""

import time
import os
import platform
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from config import BROWSER_CONFIG, NAVIGATION_CONFIG
import logging

class BrowserManager:
    def __init__(self, viewport='desktop'):
        """
        Initialize browser manager for specified viewport
        
        Args:
            viewport (str): 'desktop' or 'mobile'
        """
        self.viewport = viewport
        self.driver = None
        self.wait = None
        self.logger = logging.getLogger(__name__)
        self.platform = platform.system().lower()
        
    def _detect_chrome_version(self):
        """Detect Chrome version for better driver compatibility"""
        try:
            if self.platform == 'windows':
                # Try multiple Chrome installation paths on Windows
                chrome_paths = [
                    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                    r'C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe'.format(os.getenv('USERNAME', '')),
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        result = subprocess.run([path, '--version'], 
                                             capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            version_line = result.stdout.strip()
                            # Extract version number
                            if 'Google Chrome' in version_line:
                                version = version_line.split()[-1]
                                self.logger.info(f"Detected Chrome version: {version}")
                                return version
            else:
                # Unix-like systems
                result = subprocess.run(['google-chrome', '--version'], 
                                     capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    if 'Google Chrome' in version_line:
                        version = version_line.split()[-1]
                        self.logger.info(f"Detected Chrome version: {version}")
                        return version
                        
        except Exception as e:
            self.logger.warning(f"Could not detect Chrome version: {str(e)}")
        
        return None
    
    def _get_windows_specific_options(self, chrome_options):
        """Add Windows-specific Chrome options"""
        if self.platform == 'windows':
            # Windows-specific options for better compatibility
            chrome_options.add_argument('--disable-gpu-sandbox')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # Handle Windows Defender and antivirus interference
            chrome_options.add_argument('--disable-extensions-except')
            chrome_options.add_argument('--disable-component-extensions-with-background-pages')
            
            # Better memory management for Windows
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=4096')
            
            # Disable logging to reduce file system issues
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            
            # Handle Windows path issues
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            
        return chrome_options
    

    
    def setup_driver(self):
        """Setup Chrome WebDriver with enhanced Windows compatibility"""
        try:
            self.logger.info(f"Setting up browser driver for {self.platform} platform")
            
            chrome_options = Options()
            
            # Set window size
            window_size = BROWSER_CONFIG['window_size'][self.viewport]
            chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
            
            # Set user agent
            user_agent = BROWSER_CONFIG['user_agent'][self.viewport]
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Basic options for better performance
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Faster loading for testing
            
            # Add Windows-specific options
            chrome_options = self._get_windows_specific_options(chrome_options)
            
            # Set headless mode if configured
            if BROWSER_CONFIG['headless']:
                chrome_options.add_argument('--headless=new')  # Use new headless mode
            
            # Try multiple strategies to get a working service
            service = None
            
            # Strategy 1: Try WebDriver Manager with version detection
            try:
                chrome_version = self._detect_chrome_version()
                if chrome_version:
                    self.logger.info(f"Using ChromeDriver for Chrome version: {chrome_version}")
                    driver_path = ChromeDriverManager(version=chrome_version).install()
                else:
                    self.logger.info("Using latest ChromeDriver")
                    driver_path = ChromeDriverManager().install()
                
                service = Service(driver_path)
                self.logger.info("WebDriver Manager strategy successful")
                
            except Exception as e:
                self.logger.warning(f"WebDriver Manager strategy failed: {str(e)}")
                
                # Strategy 2: Try system ChromeDriver
                try:
                    result = subprocess.run(['chromedriver', '--version'], 
                                         capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.logger.info("Using system ChromeDriver")
                        service = Service('chromedriver')
                    else:
                        raise Exception("System ChromeDriver not available")
                except Exception as e2:
                    self.logger.warning(f"System ChromeDriver strategy failed: {str(e2)}")
                    
                    # Strategy 3: Try WebDriver Manager without version detection
                    try:
                        self.logger.info("Trying WebDriver Manager without version detection")
                        driver_path = ChromeDriverManager().install()
                        service = Service(driver_path)
                        self.logger.info("Fallback WebDriver Manager strategy successful")
                    except Exception as e3:
                        self.logger.error(f"All driver strategies failed: {str(e3)}")
                        return False
            
            # Create driver with enhanced error handling
            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.logger.info("Driver created successfully with full options")
            except Exception as e:
                # If the driver creation fails, try with minimal options
                self.logger.warning(f"Initial driver creation failed: {str(e)}")
                
                # Try with minimal options
                minimal_options = Options()
                minimal_options.add_argument('--no-sandbox')
                minimal_options.add_argument('--disable-dev-shm-usage')
                if BROWSER_CONFIG['headless']:
                    minimal_options.add_argument('--headless=new')
                
                try:
                    self.driver = webdriver.Chrome(service=service, options=minimal_options)
                    self.logger.info("Driver created with minimal options")
                except Exception as e2:
                    self.logger.error(f"Driver creation with minimal options also failed: {str(e2)}")
                    return False
            
            # Set timeouts
            self.driver.set_page_load_timeout(NAVIGATION_CONFIG['page_load_timeout'])
            self.driver.implicitly_wait(NAVIGATION_CONFIG['implicit_wait'])
            
            # Setup wait object
            self.wait = WebDriverWait(self.driver, NAVIGATION_CONFIG['implicit_wait'])
            
            # Test the driver with a simple operation
            try:
                self.driver.get('data:text/html,<html><body>Test</body></html>')
                self.logger.info("Driver test successful")
            except Exception as e:
                self.logger.error(f"Driver test failed: {str(e)}")
                return False
            
            self.logger.info(f"Browser driver setup complete for {self.viewport} viewport on {self.platform}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser driver: {str(e)}")
            
            # Provide helpful error messages for common Windows issues
            if self.platform == 'windows':
                if "not a valid Win32 application" in str(e):
                    self.logger.error("""
                    Windows compatibility issue detected. This usually means:
                    1. ChromeDriver architecture mismatch (32-bit vs 64-bit)
                    2. Corrupted ChromeDriver download
                    3. Antivirus software blocking the driver
                    
                    Solutions:
                    1. Try running as administrator
                    2. Temporarily disable antivirus
                    3. Manually download ChromeDriver from https://chromedriver.chromium.org/
                    4. Ensure Chrome browser is up to date
                    """)
                elif "chromedriver" in str(e).lower():
                    self.logger.error("""
                    ChromeDriver issue detected. Try:
                    1. Updating Chrome browser
                    2. Clearing WebDriver Manager cache
                    3. Running: pip install --upgrade webdriver-manager
                    """)
            
            return False
    
    def navigate_to_url(self, url):
        """
        Navigate to specified URL
        
        Args:
            url (str): URL to navigate to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Inject console error listener
            self.driver.execute_script("""
                // Initialize console error storage
                window.consoleErrors = [];
                
                // Override console.error to capture errors
                const originalError = console.error;
                console.error = function(...args) {
                    // Call original console.error
                    originalError.apply(console, args);
                    
                    // Store error information
                    const errorInfo = {
                        message: args.join(' '),
                        timestamp: new Date().toISOString(),
                        stack: new Error().stack
                    };
                    window.consoleErrors.push(errorInfo);
                };
                
                // Override console.warn to capture warnings
                const originalWarn = console.warn;
                console.warn = function(...args) {
                    // Call original console.warn
                    originalWarn.apply(console, args);
                    
                    // Store warning information
                    const warnInfo = {
                        message: args.join(' '),
                        timestamp: new Date().toISOString(),
                        type: 'warning'
                    };
                    window.consoleErrors.push(warnInfo);
                };
                
                // Listen for unhandled errors
                window.addEventListener('error', function(event) {
                    const errorInfo = {
                        message: event.message || 'Unhandled error',
                        filename: event.filename,
                        lineno: event.lineno,
                        colno: event.colno,
                        timestamp: new Date().toISOString(),
                        type: 'unhandled'
                    };
                    window.consoleErrors.push(errorInfo);
                });
                
                // Listen for unhandled promise rejections
                window.addEventListener('unhandledrejection', function(event) {
                    const errorInfo = {
                        message: event.reason?.message || 'Unhandled promise rejection',
                        reason: event.reason,
                        timestamp: new Date().toISOString(),
                        type: 'unhandled_promise'
                    };
                    window.consoleErrors.push(errorInfo);
                });
            """)
            
            # Additional wait for dynamic content
            time.sleep(NAVIGATION_CONFIG['pause_between_actions'])
            
            # Handle delayed CSS loading (WP Rocket/Hummingbird optimization)
            self._handle_delayed_css()
            
            self.logger.info(f"Successfully navigated to: {url}")
            return True
            
        except TimeoutException:
            self.logger.error(f"Timeout while navigating to: {url}")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            return False
    
    def scroll_page(self, duration=30, steps=10):
        """
        Scroll through the entire page from top to bottom with smooth scrolling
        
        Args:
            duration (int): Total duration in seconds
            steps (int): Number of scroll steps
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting page scroll for {duration} seconds with {steps} steps")
            
            # Wait for page to fully load and get accurate dimensions
            time.sleep(2)
            
            # Get initial page height
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Scroll to bottom first to trigger any lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get updated page height after potential lazy loading
            updated_height = self.driver.execute_script("return document.body.scrollHeight")
            if updated_height > total_height:
                total_height = updated_height
                self.logger.info(f"Page height updated to {total_height}px after lazy loading")
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Calculate smooth scrolling parameters
            scroll_distance = total_height - viewport_height
            if scroll_distance <= 0:
                scroll_distance = total_height  # If page is shorter than viewport, scroll full height
            
            step_distance = scroll_distance / steps
            step_duration = duration / steps
            
            # Start from top
            current_position = 0
            
            # Smooth scroll from top to bottom
            for i in range(steps):
                # Calculate next position
                current_position += step_distance
                
                # Ensure we don't exceed the total height
                if current_position > total_height:
                    current_position = total_height
                
                # Use smooth scrolling
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: {current_position},
                        behavior: 'smooth'
                    }});
                """)
                
                # Wait for smooth scroll to complete
                time.sleep(step_duration)
                
                # Log progress
                progress = ((i + 1) / steps) * 100
                self.logger.info(f"Scroll progress: {progress:.1f}%")
            
            # Final scroll to ensure we reach the very bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Verify we're at the bottom
            current_scroll = self.driver.execute_script("return window.pageYOffset")
            max_scroll = self.driver.execute_script("return document.body.scrollHeight - window.innerHeight")
            
            if current_scroll >= max_scroll * 0.95:  # Allow 5% tolerance
                self.logger.info("Successfully reached page bottom")
            else:
                self.logger.warning(f"May not have reached bottom. Current: {current_scroll}, Max: {max_scroll}")
            
            self.logger.info("Page scroll completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during page scroll: {str(e)}")
            return False
    
    def take_screenshot(self, filepath, full_page=True):
        """
        Take screenshot of the current page
        
        Args:
            filepath (str): Path to save the screenshot
            full_page (bool): Whether to capture full page or viewport only
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Taking screenshot: {filepath}")
            
            if full_page:
                # Get full page dimensions
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                total_width = self.driver.execute_script("return document.body.scrollWidth")
                
                # Set window size to capture full page
                self.driver.set_window_size(total_width, total_height)
                
                # Take screenshot
                self.driver.save_screenshot(filepath)
                
                # Restore original window size
                window_size = BROWSER_CONFIG['window_size'][self.viewport]
                self.driver.set_window_size(window_size[0], window_size[1])
            else:
                # Take viewport screenshot
                self.driver.save_screenshot(filepath)
            
            self.logger.info(f"Screenshot saved: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return False
    
    def get_page_info(self):
        """
        Get basic information about the current page
        
        Returns:
            dict: Page information including title, URL, and dimensions
        """
        try:
            info = {
                'title': self.driver.title,
                'url': self.driver.current_url,
                'viewport_width': self.driver.execute_script("return window.innerWidth"),
                'viewport_height': self.driver.execute_script("return window.innerHeight"),
                'page_width': self.driver.execute_script("return document.body.scrollWidth"),
                'page_height': self.driver.execute_script("return document.body.scrollHeight")
            }
            return info
        except Exception as e:
            self.logger.error(f"Error getting page info: {str(e)}")
            return {}
    
    def close(self):
        """Close the browser and cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def get_windows_troubleshooting_info(self):
        """Get Windows-specific troubleshooting information"""
        if self.platform != 'windows':
            return {}
        
        info = {
            'platform': self.platform,
            'python_version': sys.version,
            'architecture': platform.architecture(),
            'chrome_version': self._detect_chrome_version(),
            'webdriver_manager_cache': os.path.expanduser('~/.wdm'),
            'temp_dir': os.environ.get('TEMP', ''),
            'user_profile': os.environ.get('USERPROFILE', ''),
        }
        
        # Check if Chrome is installed
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe'.format(os.getenv('USERNAME', '')),
        ]
        
        chrome_installed = False
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_installed = True
                info['chrome_path'] = path
                break
        
        info['chrome_installed'] = chrome_installed
        
        return info

    def _handle_delayed_css(self):
        """
        Handle delayed CSS loading for WP Rocket/Hummingbird optimization
        
        This method detects and triggers delayed CSS loading by:
        1. Checking for delayed stylesheet elements
        2. Triggering user interaction events
        3. Directly setting href attributes for delayed stylesheets
        """
        try:
            self.logger.info("Checking for delayed CSS...")
            
            # Check if delayed CSS is present
            has_delayed_css = self.driver.execute_script("""
                return document.querySelectorAll('link[data-wphbdelayedstyle]').length > 0;
            """)
            
            self.logger.info(f"Delayed CSS elements found: {has_delayed_css}")
            
            if has_delayed_css:
                self.logger.info("Detected delayed CSS (WP Rocket/Hummingbird), triggering user events...")
                
                # Get count of delayed stylesheets
                delayed_count = self.driver.execute_script("""
                    return document.querySelectorAll('link[data-wphbdelayedstyle]').length;
                """)
                self.logger.info(f"Found {delayed_count} delayed stylesheets")
                
                # Trigger events that would normally load delayed CSS
                events = ['keydown', 'mousemove', 'wheel', 'touchmove', 'touchstart', 'touchend']
                for event in events:
                    self.driver.execute_script(f"""
                        window.dispatchEvent(new Event('{event}', {{ bubbles: true }}));
                    """)
                
                # Directly trigger the delayed stylesheet loading
                self.driver.execute_script("""
                    const delayedLinks = document.querySelectorAll('link[data-wphbdelayedstyle]');
                    delayedLinks.forEach(link => {
                        link.setAttribute('href', link.getAttribute('data-wphbdelayedstyle'));
                    });
                """)
                
                # Wait for the delayed CSS to load
                time.sleep(3)
                
                # Check if CSS is actually applied to the page
                css_applied = self.driver.execute_script("""
                    const computedStyles = window.getComputedStyle(document.body);
                    return computedStyles.fontFamily !== 'serif' && 
                           computedStyles.fontFamily !== 'Times' &&
                           computedStyles.fontSize !== '16px';
                """)
                
                if css_applied:
                    self.logger.info("Delayed CSS successfully loaded and applied")
                else:
                    self.logger.warning("Delayed CSS may not be fully applied")
            else:
                self.logger.info("No delayed CSS detected")
                    
        except Exception as e:
            self.logger.error(f"Error handling delayed CSS: {str(e)}")

    def get_console_errors(self):
        """
        Get console errors from the page
        
        Returns:
            dict: Console error information
        """
        try:
            # Execute JavaScript to get console errors
            console_errors = self.driver.execute_script("""
                // Return any console errors that might be stored
                return window.consoleErrors || [];
            """)
            
            # Also try to get any error messages from the page
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [id*='error'], .alert-danger, .error-message, .error, [data-error]")
            page_errors = []
            
            for element in error_elements:
                try:
                    text = element.text.strip()
                    if text:
                        page_errors.append({
                            'message': text,
                            'element': element.tag_name,
                            'timestamp': time.time()
                        })
                except:
                    continue
            
            # Get browser console logs using CDP (Chrome DevTools Protocol)
            try:
                logs = self.driver.get_log('browser')
                browser_logs = []
                for log in logs:
                    if log['level'] in ['SEVERE', 'WARNING']:
                        browser_logs.append({
                            'message': log['message'],
                            'level': log['level'],
                            'timestamp': log['timestamp']
                        })
            except Exception as e:
                self.logger.warning(f"Could not get browser logs: {str(e)}")
                browser_logs = []
            
            total_errors = len(console_errors) + len(page_errors) + len(browser_logs)
            return {
                'console_errors': console_errors,
                'page_errors': page_errors,
                'browser_logs': browser_logs,
                'total_errors': total_errors,
                'capture_timestamp': time.time(),
                'has_errors': total_errors > 0,
                'error_types': {
                    'console_errors': len(console_errors),
                    'page_errors': len(page_errors),
                    'browser_logs': len(browser_logs)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting console errors: {str(e)}")
            return {
                'console_errors': [], 
                'page_errors': [], 
                'browser_logs': [], 
                'total_errors': 0,
                'capture_timestamp': time.time(),
                'has_errors': False,
                'capture_error': str(e),
                'error_types': {
                    'console_errors': 0,
                    'page_errors': 0,
                    'browser_logs': 0
                }
            }

    def scroll_and_capture_errors(self, duration=10):
        """
        Scroll through the page and capture any errors that appear
        
        Args:
            duration (int): Duration to scroll in seconds
            
        Returns:
            dict: Error information collected during scroll
        """
        try:
            self.logger.info(f"Starting error capture scroll for {duration} seconds")
            
            # Initialize error tracking
            all_errors = {
                'console_errors': [],
                'page_errors': [],
                'browser_logs': [],
                'scroll_errors': [],
                'capture_timestamp': time.time(),
                'capture_status': 'success',
                'total_errors': 0,
                'error_summary': {
                    'has_errors': False,
                    'error_types_found': [],
                    'scroll_positions_with_errors': []
                }
            }
            
            # Get initial page height
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Scroll to bottom first to trigger any lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get updated page height after potential lazy loading
            updated_height = self.driver.execute_script("return document.body.scrollHeight")
            if updated_height > total_height:
                total_height = updated_height
                self.logger.info(f"Page height updated to {total_height}px after lazy loading")
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Calculate scroll parameters
            scroll_distance = total_height - viewport_height
            if scroll_distance <= 0:
                scroll_distance = total_height
            
            steps = 10
            step_distance = scroll_distance / steps
            step_duration = duration / steps
            
            # Start from top
            current_position = 0
            
            # Smooth scroll from top to bottom and capture errors
            for i in range(steps):
                # Calculate next position
                current_position += step_distance
                
                # Ensure we don't exceed the total height
                if current_position > total_height:
                    current_position = total_height
                
                # Use smooth scrolling
                self.driver.execute_script(f"""
                    window.scrollTo({{
                        top: {current_position},
                        behavior: 'smooth'
                    }});
                """)
                
                # Wait for smooth scroll to complete
                time.sleep(step_duration)
                
                # Capture errors at this scroll position
                current_errors = self.get_console_errors()
                if current_errors['total_errors'] > 0:
                    all_errors['scroll_errors'].append({
                        'position': current_position,
                        'errors': current_errors
                    })
                
                # Log progress
                progress = ((i + 1) / steps) * 100
                self.logger.info(f"Error capture scroll progress: {progress:.1f}%")
            
            # Final scroll to ensure we reach the very bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Final error capture
            final_errors = self.get_console_errors()
            all_errors['console_errors'] = final_errors['console_errors']
            all_errors['page_errors'] = final_errors['page_errors']
            all_errors['browser_logs'] = final_errors['browser_logs']
            
            # Calculate total errors and update summary
            total_errors = len(all_errors['console_errors']) + len(all_errors['page_errors']) + len(all_errors['browser_logs']) + len(all_errors['scroll_errors'])
            all_errors['total_errors'] = total_errors
            
            # Update error summary
            all_errors['error_summary']['has_errors'] = total_errors > 0
            
            # Track error types found
            error_types = set()
            if all_errors['console_errors']:
                error_types.add('console_errors')
            if all_errors['page_errors']:
                error_types.add('page_errors')
            if all_errors['browser_logs']:
                error_types.add('browser_logs')
            if all_errors['scroll_errors']:
                error_types.add('scroll_errors')
            
            all_errors['error_summary']['error_types_found'] = list(error_types)
            
            # Track scroll positions with errors
            for scroll_error in all_errors['scroll_errors']:
                all_errors['error_summary']['scroll_positions_with_errors'].append(scroll_error['position'])
            
            if total_errors > 0:
                self.logger.info(f"Error capture scroll completed. Found {total_errors} total errors across {len(all_errors['scroll_errors'])} scroll positions")
            else:
                self.logger.info(f"Error capture scroll completed. No errors found - page appears to be error-free")
            
            return all_errors
            
        except Exception as e:
            self.logger.error(f"Error during error capture scroll: {str(e)}")
            return {
                'console_errors': [], 
                'page_errors': [], 
                'browser_logs': [],
                'scroll_errors': [],
                'capture_timestamp': time.time(),
                'capture_status': 'failed',
                'capture_error': str(e),
                'total_errors': 0,
                'error_summary': {
                    'has_errors': False,
                    'error_types_found': [],
                    'scroll_positions_with_errors': []
                }
            } 