"""
Configuration settings for the Website Optimization Pre-Check Tool
"""

import os
from datetime import datetime

# Browser Configuration
BROWSER_CONFIG = {
    'headless': True,  # Set to True for headless mode (default)
    'window_size': {
        'desktop': (1920, 1080),
        'mobile': (375, 667)  # iPhone 6/7/8 size
    },
    'user_agent': {
        'desktop': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'mobile': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    }
}

# Video Recording Configuration
VIDEO_CONFIG = {
    'fps': 30,
    'duration': 30,  # seconds per page
    'scroll_pause': 0.3,  # seconds to pause between scrolls (reduced for smoother video)
    'scroll_steps': 30,  # number of scroll steps per page (increased for smoother video recording)
    'output_format': 'mp4',
    'codec': 'libx264'  # Better codec for color accuracy
}

# Screenshot Configuration
SCREENSHOT_CONFIG = {
    'full_page': True,
    'quality': 95,
    'format': 'PNG',
    'delay': 3  # seconds to wait before taking screenshot
}

# PageSpeed Configuration
PAGESPEED_CONFIG = {
    'base_url': 'https://pagespeed.web.dev/',
    'wait_time': 10,  # seconds to wait for PageSpeed results
    'strategies': ['mobile', 'desktop']
}

# Navigation Configuration
NAVIGATION_CONFIG = {
    'page_load_timeout': 30,
    'implicit_wait': 10,
    'scroll_behavior': 'smooth',
    'pause_between_actions': 1
}

# Output Configuration
OUTPUT_CONFIG = {
    'base_dir': 'outputs',
    'timestamp_format': '%Y-%m-%d_%H-%M-%S',
    'subdirs': {
        'videos': 'videos',
        'screenshots': 'screenshots',
        'pagespeed': 'pagespeed'
    },
    'file_naming': {
        'separator': '_',
        'suffixes': {
            'desktop': 'desktop',
            'mobile': 'mobile'
        }
    }
}

# URL Validation
URL_CONFIG = {
    'allowed_schemes': ['http', 'https'],
    'max_urls': 4,
    'default_urls': [
        'https://www.google.com',
        'https://www.github.com',
        'https://www.stackoverflow.com',
        'https://www.wikipedia.org'
    ]
}

def get_output_directory():
    """Generate output directory with timestamp"""
    timestamp = datetime.now().strftime(OUTPUT_CONFIG['timestamp_format'])
    return os.path.join(OUTPUT_CONFIG['base_dir'], timestamp)

def create_directory_structure(base_dir):
    """Create the complete directory structure for outputs"""
    subdirs = OUTPUT_CONFIG['subdirs']
    
    for category in ['videos', 'screenshots', 'pagespeed']:
        for viewport in ['desktop', 'mobile']:
            path = os.path.join(base_dir, subdirs[category], viewport)
            os.makedirs(path, exist_ok=True)
    
    return base_dir

def sanitize_filename(url, viewport):
    """Convert URL to safe filename"""
    # Remove protocol and common TLDs
    domain = url.replace('https://', '').replace('http://', '').replace('www.', '')
    domain = domain.replace('.com', '').replace('.org', '').replace('.net', '')
    
    # Replace dots, slashes, and special characters
    domain = domain.replace('.', '_').replace('-', '_').replace('/', '_')
    
    # Add viewport suffix
    suffix = OUTPUT_CONFIG['file_naming']['suffixes'][viewport]
    
    return f"{domain}_{suffix}" 