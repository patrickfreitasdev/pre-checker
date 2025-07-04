#!/usr/bin/env python3
"""
Setup script for Website Optimization Pre-Check Tool
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_chrome():
    """Check if Chrome browser is available"""
    print("\n🌐 Checking Chrome browser...")
    
    # Common Chrome paths
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",    # Windows
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe", # Windows 32-bit
        "/usr/bin/google-chrome",  # Linux
        "/usr/bin/chromium-browser",  # Linux Chromium
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Chrome found at: {path}")
            return True
    
    print("⚠️  Chrome not found in common locations")
    print("Please install Google Chrome from: https://www.google.com/chrome/")
    return False

def create_output_directory():
    """Create output directory"""
    print("\n📁 Creating output directory...")
    
    try:
        os.makedirs("outputs", exist_ok=True)
        print("✅ Output directory created")
        return True
    except Exception as e:
        print(f"❌ Failed to create output directory: {e}")
        return False

def test_imports():
    """Test if all modules can be imported"""
    print("\n🧪 Testing imports...")
    
    modules = [
        "selenium",
        "cv2",
        "PIL",
        "requests",
        "rich",
        "webdriver_manager"
    ]
    
    failed_imports = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Failed to import: {', '.join(failed_imports)}")
        return False
    
    return True

def run_quick_test():
    """Run a quick test to verify everything works"""
    print("\n🚀 Running quick test...")
    
    try:
        # Test browser manager
        from browser_manager import BrowserManager
        
        with BrowserManager(viewport='desktop') as browser:
            success = browser.navigate_to_url("https://www.google.com")
            if success:
                print("✅ Browser test successful")
                return True
            else:
                print("❌ Browser test failed")
                return False
                
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Website Optimization Pre-Check Tool Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check Chrome
    if not check_chrome():
        print("\n⚠️  Setup can continue, but Chrome is required for full functionality")
    
    # Create output directory
    if not create_output_directory():
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("\n⚠️  Some dependencies may not be properly installed")
    
    # Run quick test
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\n📖 Next steps:")
    print("1. Run the tool: python main.py")
    print("2. Or try the example: python example.py")
    print("3. Check the README.md for more information")
    
    # Ask if user wants to run quick test
    try:
        response = input("\n🧪 Run quick test? (y/N): ").lower()
        if response in ['y', 'yes']:
            if run_quick_test():
                print("🎉 Everything is working correctly!")
            else:
                print("⚠️  Quick test failed. Check the logs for details.")
    except KeyboardInterrupt:
        print("\n👋 Setup completed!")

if __name__ == "__main__":
    main() 