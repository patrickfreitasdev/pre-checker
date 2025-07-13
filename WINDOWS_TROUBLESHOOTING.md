# Windows Compatibility Troubleshooting Guide

This guide helps resolve Windows-specific issues with the Website Optimization Pre-Check Tool.

## Common Issues and Solutions

### 1. "not a valid Win32 application" Error

**Symptoms:**
```
[WinError 193] %1 is not a valid Win32 application
```

**Causes:**
- ChromeDriver architecture mismatch (32-bit vs 64-bit)
- Corrupted ChromeDriver download
- Antivirus software blocking the driver

**Solutions:**

#### Option A: Run as Administrator
1. Right-click on your command prompt/PowerShell
2. Select "Run as administrator"
3. Navigate to your project directory
4. Run the script again

#### Option B: Temporarily Disable Antivirus
1. Temporarily disable Windows Defender or your antivirus software
2. Run the script
3. Re-enable antivirus after testing

#### Option C: Clear WebDriver Manager Cache
```bash
# Remove the cache directory
rmdir /s /q "%USERPROFILE%\.wdm"

# Or manually delete the folder:
# C:\Users\[YourUsername]\.wdm
```

#### Option D: Update Chrome Browser
1. Open Chrome
2. Go to `chrome://settings/help`
3. Update to the latest version
4. Restart Chrome

#### Option E: Manual ChromeDriver Installation
1. Go to https://chromedriver.chromium.org/
2. Download the version matching your Chrome browser
3. Extract the `chromedriver.exe` file
4. Place it in a directory in your PATH or in your project directory

### 2. ChromeDriver Not Found

**Symptoms:**
```
ChromeDriver not found at: [path]
```

**Solutions:**

#### Option A: Reinstall webdriver-manager
```bash
pip uninstall webdriver-manager
pip install webdriver-manager==4.0.1
```

#### Option B: Use System ChromeDriver
1. Download ChromeDriver from https://chromedriver.chromium.org/
2. Extract to a directory in your PATH (e.g., `C:\Windows\System32`)
3. Verify installation: `chromedriver --version`

### 3. Chrome Browser Not Detected

**Symptoms:**
```
Could not detect Chrome version
```

**Solutions:**

#### Option A: Install Chrome Browser
1. Download Chrome from https://www.google.com/chrome/
2. Install with default settings
3. Restart your computer

#### Option B: Check Chrome Installation Path
The tool looks for Chrome in these locations:
- `C:\Program Files\Google\Chrome\Application\chrome.exe`
- `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
- `C:\Users\[Username]\AppData\Local\Google\Chrome\Application\chrome.exe`

### 4. Permission Denied Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

#### Option A: Run as Administrator
1. Right-click on your terminal
2. Select "Run as administrator"
3. Navigate to your project directory
4. Run the script

#### Option B: Check File Permissions
1. Right-click on the project folder
2. Select "Properties"
3. Go to "Security" tab
4. Ensure your user has "Full control" permissions

### 5. Memory Issues

**Symptoms:**
```
OutOfMemoryError or browser crashes
```

**Solutions:**

#### Option A: Reduce Memory Usage
The tool now includes Windows-specific memory management options:
- `--memory-pressure-off`
- `--max_old_space_size=4096`

#### Option B: Close Other Applications
1. Close unnecessary applications
2. Restart your computer
3. Try running the script again

## Testing Your Setup

Run the Windows compatibility test:

```bash
python test_windows_compatibility.py
```

This will:
1. Detect your platform and Chrome version
2. Test driver setup with multiple strategies
3. Provide detailed troubleshooting information
4. Test basic browser functionality

## Environment Requirements

### Minimum Requirements
- Windows 10 or later
- Python 3.8 or later
- Chrome browser (latest version)
- 4GB RAM minimum
- 1GB free disk space

### Recommended Requirements
- Windows 11
- Python 3.9 or later
- Chrome browser (latest version)
- 8GB RAM
- 2GB free disk space
- SSD storage

## Advanced Troubleshooting

### Check System Information
```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check Chrome version
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version
```

### Verify Dependencies
```bash
# Install/upgrade all dependencies
pip install -r requirements.txt --upgrade

# Check installed packages
pip list
```

### Debug Mode
Run with verbose logging:
```bash
python -u main.py --verbose
```

### Manual Testing
Test each component individually:
```bash
# Test browser manager only
python test_windows_compatibility.py

# Test with specific URL
python main.py --url https://www.google.com
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** - Look for detailed error messages
2. **Run the test script** - Use `test_windows_compatibility.py`
3. **Check system requirements** - Ensure your system meets minimum requirements
4. **Try minimal configuration** - The tool will automatically fall back to minimal options

## Common Workarounds

### If ChromeDriver Still Fails
1. Try running in non-headless mode (edit `config.py` and set `'headless': False`)
2. Use a different Chrome profile
3. Try running with minimal Chrome options

### If Antivirus Continues to Block
1. Add the project directory to antivirus exclusions
2. Add `chromedriver.exe` to antivirus whitelist
3. Temporarily disable real-time protection during testing

### If Memory Issues Persist
1. Close other applications
2. Restart your computer
3. Try running with reduced window size in `config.py`

## Version Compatibility

| Component | Minimum Version | Recommended Version |
|-----------|----------------|-------------------|
| Python | 3.8 | 3.9+ |
| Chrome Browser | 90+ | Latest |
| ChromeDriver | 90+ | Latest |
| webdriver-manager | 3.8.0 | 4.0.1+ |
| selenium | 4.0.0 | 4.15.2+ |

## Support

For additional help:
1. Check the main README.md for general usage
2. Review the logs for specific error messages
3. Test with the provided test script
4. Ensure all system requirements are met 