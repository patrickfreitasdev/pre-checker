"""
Browser Manager for Website Optimization Pre-Check Tool
Handles Selenium WebDriver setup and management
"""

import time
import os
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
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate configuration"""
        try:
            chrome_options = Options()
            
            # Set window size
            window_size = BROWSER_CONFIG['window_size'][self.viewport]
            chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
            
            # Set user agent
            user_agent = BROWSER_CONFIG['user_agent'][self.viewport]
            chrome_options.add_argument(f'--user-agent={user_agent}')
            
            # Additional options for better performance
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Faster loading for testing
            
            # Set headless mode if configured
            if BROWSER_CONFIG['headless']:
                chrome_options.add_argument('--headless')
            
            # Setup service with automatic driver management
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(NAVIGATION_CONFIG['page_load_timeout'])
            self.driver.implicitly_wait(NAVIGATION_CONFIG['implicit_wait'])
            
            # Setup wait object
            self.wait = WebDriverWait(self.driver, NAVIGATION_CONFIG['implicit_wait'])
            
            self.logger.info(f"Browser driver setup complete for {self.viewport} viewport")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser driver: {str(e)}")
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
            
            # Additional wait for dynamic content
            time.sleep(NAVIGATION_CONFIG['pause_between_actions'])
            
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