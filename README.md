# Website Optimization Pre-Check Tool

> **⚠️ IMPORTANT DISCLAIMER**  
> This tool is **AI-generated code** and is intended for **educational and testing purposes only**.  
> **DO NOT USE IN PRODUCTION** 

A comprehensive website analysis tool that automates performance testing, visual recording, and PageSpeed analysis for web optimization projects.

## 🚀 Features

### 📊 Performance Analysis
- **PageSpeed Insights Integration** - Official Google PageSpeed API with fallback analyzer
- **Multi-device Testing** - Desktop and mobile viewport analysis
- **Visual Score Charts** - Professional performance score visualizations
- **Comprehensive Metrics** - Load times, DOM ready, first paint, page size analysis

### 🎥 Visual Recording
- **Smooth Video Capture** - High-quality MP4 recordings of page interactions
- **Full Page Coverage** - Complete scroll from header to footer
- **Dual Viewport Support** - Desktop and mobile recordings
- **Lazy Loading Detection** - Intelligent content loading analysis

### 📸 Screenshot Generation
- **Full Page Screenshots** - Complete page captures for both viewports
- **High Resolution** - Professional quality images for analysis
- **Organized Output** - Structured file organization by viewport

### 🎯 Modular Architecture
- **Selective Testing** - Run specific modules only (score, screenshot, record)
- **Flexible Configuration** - Customizable analysis parameters
- **Batch Processing** - Analyze multiple URLs simultaneously (up to 4)

## 📋 Prerequisites

- **Python 3.8+**
- **Chrome Browser** (for Selenium automation)
- **FFmpeg** (for video processing)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pre-check
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (if not already installed)
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

## 🚀 Usage

### Basic Usage

```bash
# Interactive mode
python main.py

# Command line with URLs
python main.py --urls "https://example.com,https://google.com"

# Headless mode (no browser UI)
python main.py --urls "example.com" --headless
```

### Module-Specific Testing

```bash
# PageSpeed analysis only
python main.py --urls "example.com" --score --headless

# Screenshots only
python main.py --urls "example.com" --screenshot --headless

# Video recording only
python main.py --urls "example.com" --record --headless

# All modules (default)
python main.py --urls "example.com" --all --headless
```

### Advanced Usage

```bash
# Multiple URLs with verbose logging
python main.py --urls "site1.com,site2.com,site3.com" --verbose --headless

# Single URL with all modules
python main.py --urls "example.com" --all --headless
```

## 📁 Output Structure

```
outputs/
├── YYYY-MM-DD_HH-MM-SS/
│   ├── videos/
│   │   ├── desktop/
│   │   │   └── example_com__desktop.mp4
│   │   └── mobile/
│   │       └── example_com__mobile.mp4
│   ├── screenshots/
│   │   ├── desktop/
│   │   │   └── example_com__desktop.png
│   │   └── mobile/
│   │       └── example_com__mobile.png
│   ├── pagespeed/
│   │   ├── desktop/
│   │   │   ├── example_com__desktop_pagespeed_results.json
│   │   │   ├── example_com__desktop_pagespeed_summary.txt
│   │   │   ├── example_com__desktop_pagespeed_chart.txt
│   │   │   └── example_com__desktop_pagespeed_score.png
│   │   └── mobile/
│   │       └── [similar files for mobile]
│   ├── summary_report.txt
│   └── analysis.log
```

## 📊 Sample Output

### Console Results
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ URL                                              ┃ Desktop    ┃ Mobile      ┃ Avg Score ┃ Files ┃ Errors ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ https://example.com                              │ 85         │ 72          │ 78.5      │ 10    │ 0      │
└──────────────────────────────────────────────────┴────────────┴─────────────┴───────────┴───────┴────────┘

Overall Averages (across 1 URLs):
  Desktop Score: 85.0
  Mobile Score: 72.0
  Overall Average: 78.5
  Total Files Generated: 10
  Total Errors: 0
```

### Generated Files
- **Videos**: MP4 recordings of page scrolling
- **Screenshots**: Full-page PNG captures
- **PageSpeed Results**: JSON data, text reports, and visual charts
- **Summary Report**: Comprehensive analysis overview

## ⚙️ Configuration

### Environment Variables
```bash
# Optional: Google PageSpeed API Key (for higher quotas)
PAGESPEED_API_KEY=your_api_key_here
```

### Configuration Files
- `config.py` - Main configuration settings
- `requirements.txt` - Python dependencies

## 🔧 Customization

### Video Settings
```python
# config.py
VIDEO_CONFIG = {
    'duration': 30,        # Recording duration in seconds
    'fps': 30,            # Frames per second
    'scroll_steps': 30,   # Number of scroll steps
    'output_format': 'mp4'
}
```

### Browser Settings
```python
# config.py
BROWSER_CONFIG = {
    'headless': False,    # Show browser UI
    'window_size': {
        'desktop': (1920, 1080),
        'mobile': (500, 800)
    }
}
```

## 🚨 Important Notes

### ⚠️ Production Use Warning
- **This is AI-generated code** - Review thoroughly before production use
- **Security implications** - Web scraping and automation can have security risks
- **Rate limiting** - Respect website terms of service and rate limits
- **Legal compliance** - Ensure compliance with local laws and regulations

### 🔒 Security Considerations
- **API Keys** - Store sensitive keys in environment variables
- **Browser Automation** - Be aware of potential security implications
- **Data Privacy** - Ensure compliance with data protection regulations

### 📈 Performance Considerations
- **Resource Usage** - Video recording and browser automation are resource-intensive
- **Network Impact** - Multiple concurrent analyses may impact network performance
- **Storage** - Generated files can be large; monitor disk space

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Issues**
```bash
# Clear WebDriver cache
rm -rf ~/.wdm/
```

**FFmpeg Not Found**
```bash
# Verify FFmpeg installation
ffmpeg -version
```

**Permission Errors**
```bash
# Ensure write permissions to output directory
chmod 755 outputs/
```

**Memory Issues**
```bash
# Reduce video quality or duration in config.py
VIDEO_CONFIG['fps'] = 15  # Lower FPS
VIDEO_CONFIG['duration'] = 20  # Shorter duration
``