"""
Video Recorder for Website Optimization Pre-Check Tool
Handles screen recording during browser navigation
"""

import cv2
import numpy as np
import time
import threading
import os
from datetime import datetime
from config import VIDEO_CONFIG
import logging
import mss
import imageio

class VideoRecorder:
    def __init__(self, output_path, fps=30, duration=30):
        """
        Initialize video recorder
        
        Args:
            output_path (str): Path to save the video file
            fps (int): Frames per second
            duration (int): Recording duration in seconds
        """
        self.output_path = output_path
        self.fps = fps
        self.duration = duration
        self.is_recording = False
        self.video_writer = None
        self.recording_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Video codec settings
        self.fourcc = cv2.VideoWriter_fourcc(*VIDEO_CONFIG['codec'])
        
    def start_recording(self):
        """Start video recording in a separate thread"""
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return False
            
        try:
            # Get screen dimensions (you might need to adjust this for your system)
            screen_width = 1920
            screen_height = 1080
            
            # Create video writer
            self.video_writer = cv2.VideoWriter(
                self.output_path,
                self.fourcc,
                self.fps,
                (screen_width, screen_height)
            )
            
            if not self.video_writer.isOpened():
                self.logger.error("Failed to open video writer")
                return False
            
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_screen)
            self.recording_thread.start()
            
            self.logger.info(f"Started video recording: {self.output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting video recording: {str(e)}")
            return False
    
    def _record_screen(self):
        """Internal method to record screen"""
        try:
            start_time = time.time()
            frame_count = 0
            
            while self.is_recording and (time.time() - start_time) < self.duration:
                # Capture screen (this is a simplified version)
                # In a real implementation, you might use:
                # - pyautogui.screenshot() for cross-platform
                # - mss library for better performance
                # - platform-specific screen capture APIs
                
                # For now, we'll create a placeholder frame
                frame = self._create_placeholder_frame()
                
                if frame is not None:
                    self.video_writer.write(frame)
                    frame_count += 1
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
            
            self.logger.info(f"Recording completed. Frames captured: {frame_count}")
            
        except Exception as e:
            self.logger.error(f"Error during recording: {str(e)}")
        finally:
            self.stop_recording()
    
    def _create_placeholder_frame(self):
        """
        Create a placeholder frame for demonstration
        In a real implementation, this would capture the actual screen
        """
        try:
            # Create a simple colored frame with timestamp
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (255, 255, 255), 2)
            
            # Add recording indicator
            cv2.putText(frame, "REC", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (0, 0, 255), 2)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error creating placeholder frame: {str(e)}")
            return None
    
    def stop_recording(self):
        """Stop video recording"""
        self.is_recording = False
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.logger.info("Video recording stopped")
    
    def is_active(self):
        """Check if recording is currently active"""
        return self.is_recording
    
    def get_recording_info(self):
        """Get information about the current recording"""
        return {
            'output_path': self.output_path,
            'fps': self.fps,
            'duration': self.duration,
            'is_recording': self.is_recording,
            'file_size': os.path.getsize(self.output_path) if os.path.exists(self.output_path) else 0
        }

class ScreenRecorder:
    """
    Enhanced screen recorder using pyautogui for actual screen capture
    Note: This requires additional setup for screen capture
    """
    
    def __init__(self, output_path, fps=30, duration=30):
        self.output_path = output_path
        self.fps = fps
        self.duration = duration
        self.is_recording = False
        self.video_writer = None
        self.recording_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Try to import pyautogui for screen capture
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.has_pyautogui = True
        except ImportError:
            self.logger.warning("pyautogui not available. Using placeholder frames.")
            self.has_pyautogui = False
    
    def start_recording(self):
        """Start screen recording"""
        if self.is_recording:
            return False
            
        try:
            # Get screen size
            if self.has_pyautogui:
                screen_width, screen_height = self.pyautogui.size()
            else:
                screen_width, screen_height = 1920, 1080
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CONFIG['codec'])
            self.video_writer = cv2.VideoWriter(
                self.output_path,
                fourcc,
                self.fps,
                (screen_width, screen_height)
            )
            
            if not self.video_writer.isOpened():
                self.logger.error("Failed to open video writer")
                return False
            
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_screen)
            self.recording_thread.start()
            
            self.logger.info(f"Started screen recording: {self.output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting screen recording: {str(e)}")
            return False
    
    def _record_screen(self):
        """Record actual screen content"""
        try:
            start_time = time.time()
            frame_count = 0
            
            while self.is_recording and (time.time() - start_time) < self.duration:
                if self.has_pyautogui:
                    # Capture actual screen
                    screenshot = self.pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    # Use placeholder frame
                    frame = self._create_placeholder_frame()
                
                if frame is not None:
                    self.video_writer.write(frame)
                    frame_count += 1
                
                time.sleep(1.0 / self.fps)
            
            self.logger.info(f"Screen recording completed. Frames captured: {frame_count}")
            
        except Exception as e:
            self.logger.error(f"Error during screen recording: {str(e)}")
        finally:
            self.stop_recording()
    
    def _create_placeholder_frame(self):
        """Create placeholder frame when pyautogui is not available"""
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"Screen Recording - {timestamp}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame
    
    def stop_recording(self):
        """Stop screen recording"""
        self.is_recording = False
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.logger.info("Screen recording stopped")
    
    def is_active(self):
        """Check if recording is active"""
        return self.is_recording 

class MSSVideoRecorder:
    def __init__(self, output_path, fps=30, duration=30):
        self.output_path = output_path
        self.fps = fps
        self.duration = duration
        self.is_recording = False
        self.recording_thread = None
        self.logger = logging.getLogger(__name__)

    def start_recording(self):
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return False
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_screen)
        self.recording_thread.start()
        self.logger.info(f"Started video recording: {self.output_path}")
        return True

    def _record_screen(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                frames = []
                start_time = time.time()
                frame_interval = 1.0 / self.fps
                while self.is_recording and (time.time() - start_time) < self.duration:
                    img = sct.grab(monitor)
                    frame = np.array(img)
                    frames.append(frame)
                    time.sleep(frame_interval)
                # Ensure output directory exists
                os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
                # Write video
                imageio.mimsave(self.output_path, frames, fps=self.fps)
                self.logger.info(f"Recording completed. Frames captured: {len(frames)}")
        except Exception as e:
            self.logger.error(f"Error during recording: {str(e)}")
        finally:
            self.is_recording = False

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        self.logger.info("Video recording stopped") 

class BrowserVideoRecorder:
    """
    Browser-based video recorder that captures website content using Selenium screenshots
    """
    
    def __init__(self, browser_driver, output_path, fps=30, duration=30):
        self.browser_driver = browser_driver
        self.output_path = output_path
        self.fps = fps
        self.duration = duration
        self.is_recording = False
        self.recording_thread = None
        self.logger = logging.getLogger(__name__)

    def start_recording(self):
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return False
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_browser)
        self.recording_thread.start()
        self.logger.info(f"Started browser video recording: {self.output_path}")
        return True

    def _record_browser(self):
        try:
            frames = []
            start_time = time.time()
            frame_interval = 1.0 / self.fps
            
            while self.is_recording:
                try:
                    # Take screenshot of the browser window
                    screenshot = self.browser_driver.get_screenshot_as_png()
                    
                    # Convert PNG to numpy array
                    nparr = np.frombuffer(screenshot, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        frames.append(frame)
                    
                    time.sleep(frame_interval)
                    
                except Exception as e:
                    self.logger.warning(f"Error capturing frame: {str(e)}")
                    time.sleep(frame_interval)
                    continue
            
            if frames:
                # Ensure output directory exists
                os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
                # Write video
                imageio.mimsave(self.output_path, frames, fps=self.fps)
                self.logger.info(f"Browser recording completed. Frames captured: {len(frames)}")
            else:
                self.logger.warning("No frames captured during recording")
                
        except Exception as e:
            self.logger.error(f"Error during browser recording: {str(e)}")
        finally:
            self.is_recording = False

    def stop_recording(self):
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        self.logger.info("Browser video recording stopped")

    def is_active(self):
        return self.is_recording 