#!/usr/bin/env python3
"""
Test script for Windows compatibility improvements
"""

import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager

def test_windows_compatibility():
    """Test Windows compatibility features"""
    print("Testing Windows compatibility improvements...")
    
    # Create browser manager
    browser = BrowserManager(viewport='desktop')
    
    # Test platform detection
    print(f"Platform detected: {browser.platform}")
    
    # Test Chrome version detection
    chrome_version = browser._detect_chrome_version()
    print(f"Chrome version detected: {chrome_version}")
    
    # Test Windows troubleshooting info
    if browser.platform == 'windows':
        troubleshooting_info = browser.get_windows_troubleshooting_info()
        print("Windows troubleshooting information:")
        for key, value in troubleshooting_info.items():
            print(f"  {key}: {value}")
    
    # Test driver setup
    print("\nTesting driver setup...")
    success = browser.setup_driver()
    
    if success:
        print("✅ Driver setup successful!")
        
        # Test basic functionality
        try:
            page_info = browser.get_page_info()
            print(f"✅ Page info test successful: {page_info.get('title', 'N/A')}")
        except Exception as e:
            print(f"❌ Page info test failed: {str(e)}")
        
        # Clean up
        browser.close()
        print("✅ Browser cleanup successful!")
    else:
        print("❌ Driver setup failed!")
        
        # Provide troubleshooting information
        if browser.platform == 'windows':
            print("\nTroubleshooting suggestions:")
            print("1. Try running as administrator")
            print("2. Temporarily disable antivirus software")
            print("3. Update Chrome browser to latest version")
            print("4. Clear WebDriver Manager cache: rm -rf ~/.wdm")
            print("5. Reinstall webdriver-manager: pip install --upgrade webdriver-manager")
    
    return success

if __name__ == "__main__":
    try:
        success = test_windows_compatibility()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        sys.exit(1) 