#!/usr/bin/env python3
"""
TrichShot
A real-time hand detection system that warns when hands are near the face area.
Featuring smart camera detection and external camera prioritization.
"""

import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import subprocess
from typing import Optional, Tuple, List, Dict

class CameraDetector:
    """Handles camera detection and prioritization"""
    
    @staticmethod
    def get_camera_info(camera_index: int) -> Dict:
        """Get detailed camera information"""
        info = {
            'index': camera_index,
            'name': 'Unknown',
            'is_external': False,
            'resolution': None,
            'working': False
        }
        
        try:
            # Try to get camera name from v4l2
            if os.path.exists(f'/dev/video{camera_index}'):
                try:
                    result = subprocess.run(
                        ['v4l2-ctl', '--device', f'/dev/video{camera_index}', '--info'],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'Card type' in line:
                                info['name'] = line.split(':')[1].strip()
                                break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            
            # Test camera functionality
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    info['working'] = True
                    info['resolution'] = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                                        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
                cap.release()
                
        except Exception as e:
            print(f"Error checking camera {camera_index}: {e}")
            
        # Heuristics to determine if camera is external
        name_lower = info['name'].lower()
        external_indicators = [
            'usb', 'logitech', 'microsoft', 'creative', 'webcam', 
            'external', 'hd pro', 'c920', 'c922', 'c930', 'c270'
        ]
        integrated_indicators = [
            'integrated', 'built-in', 'internal', 'laptop', 'chicony', 
            'realtek', 'asus', 'hp truevision', 'lenovo', 'dell'
        ]
        
        if any(indicator in name_lower for indicator in external_indicators):
            info['is_external'] = True
        elif any(indicator in name_lower for indicator in integrated_indicators):
            info['is_external'] = False
        else:
            # If we can't determine from name, higher indices are more likely external
            info['is_external'] = camera_index > 0
            
        return info
    
    @staticmethod
    def find_available_cameras() -> List[Dict]:
        """Find all available cameras and return sorted by preference"""
        cameras = []
        
        # Check common camera indices
        for i in range(10):  # Check /dev/video0 through /dev/video9
            if os.path.exists(f'/dev/video{i}'):
                camera_info = CameraDetector.get_camera_info(i)
                if camera_info['working']:
                    cameras.append(camera_info)
        
        # Sort cameras: external cameras first, then by index
        cameras.sort(key=lambda x: (not x['is_external'], x['index']))
        
        return cameras
    
    @staticmethod
    def get_preferred_camera() -> Optional[int]:
        """Get the most preferred camera index"""
        cameras = CameraDetector.find_available_cameras()
        return cameras[0]['index'] if cameras else None

class TrichShotApp:
    def __init__(self):
        # MediaPipe setup (CPU-only mode for Docker)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
            model_complexity=0  # Use simpler model for better Docker compatibility
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Video capture
        self.cap = None
        self.running = False
        self.current_camera_index = None
        
        # Warning system
        self.warning_active = False
        self.warning_window = None
        
        # Configuration
        self.danger_zone_top = 0.75    # Top 75% of screen (adjust as needed)
        self.danger_zone_bottom = 0.75  # Bottom 75% of screen
        self.warning_cooldown = 0.5    # Minimum time in seconds between warning updates
        self.last_warning_update = 0
        
        # Setup GUI
        self.setup_gui()
        
        # Detect cameras on startup
        self.detect_cameras()
        
    def detect_cameras(self):
        """Detect available cameras and update UI"""
        self.cameras = CameraDetector.find_available_cameras()
        
        if self.cameras:
            camera_info = []
            for cam in self.cameras:
                status = "External" if cam['is_external'] else "Integrated"
                resolution = f"{cam['resolution'][0]}x{cam['resolution'][1]}" if cam['resolution'] else "Unknown"
                camera_info.append(f"Camera {cam['index']}: {cam['name']} ({status}) - {resolution}")
            
            self.camera_info_text.set("\n".join(camera_info))
            self.selected_camera_var.set(self.cameras[0]['index'])  # Select preferred camera
        else:
            self.camera_info_text.set("No working cameras detected!")
        
    def setup_gui(self):
        """Setup the main control GUI"""
        self.root = tk.Tk()
        self.root.title("TrichShot -")
        self.root.geometry("500x450")
        
        # Status frame
        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.status_label = ttk.Label(status_frame, text="Status: Stopped", font=("Arial", 12))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Camera selection frame
        camera_frame = ttk.LabelFrame(status_frame, text="Camera Selection", padding="5")
        camera_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        
        self.camera_info_text = tk.StringVar(value="Detecting cameras...")
        camera_info_label = ttk.Label(camera_frame, textvariable=self.camera_info_text, 
                                    justify=tk.LEFT, font=("Courier", 9))
        camera_info_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(camera_frame, text="Selected Camera:").grid(row=1, column=0, sticky=tk.W)
        self.selected_camera_var = tk.IntVar()
        self.camera_combo = ttk.Combobox(camera_frame, textvariable=self.selected_camera_var, 
                                       state="readonly", width=10)
        self.camera_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        
        refresh_button = ttk.Button(camera_frame, text="Refresh Cameras", 
                                  command=self.refresh_cameras)
        refresh_button.grid(row=1, column=2, padx=(10, 0))
        
        # Control buttons
        control_frame = ttk.Frame(status_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", 
                                     command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", 
                                    command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(status_frame, text="Configuration", padding="5")
        config_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(config_frame, text="Danger Zone Top:").grid(row=0, column=0, sticky=tk.W)
        self.danger_top_var = tk.DoubleVar(value=self.danger_zone_top)
        danger_top_scale = ttk.Scale(config_frame, from_=0.0, to=0.5, 
                                   variable=self.danger_top_var, orient=tk.HORIZONTAL)
        danger_top_scale.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(config_frame, text="Danger Zone Bottom:").grid(row=1, column=0, sticky=tk.W)
        self.danger_bottom_var = tk.DoubleVar(value=self.danger_zone_bottom)
        danger_bottom_scale = ttk.Scale(config_frame, from_=0.5, to=1.0, 
                                      variable=self.danger_bottom_var, orient=tk.HORIZONTAL)
        danger_bottom_scale.grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Stats frame
        stats_frame = ttk.LabelFrame(status_frame, text="Session Stats", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.warnings_count_var = tk.StringVar(value="Warnings triggered: 0")
        ttk.Label(stats_frame, textvariable=self.warnings_count_var).grid(row=0, column=0)
        
        self.session_time_var = tk.StringVar(value="Session time: 00:00:00")
        ttk.Label(stats_frame, textvariable=self.session_time_var).grid(row=1, column=0)
        
        self.camera_status_var = tk.StringVar(value="Camera: Not active")
        ttk.Label(stats_frame, textvariable=self.camera_status_var).grid(row=2, column=0)
        
        # Initialize stats
        self.warnings_count = 0
        self.session_start_time = None
        
    def refresh_cameras(self):
        """Refresh camera detection"""
        self.detect_cameras()
        # Update combo box values
        if self.cameras:
            self.camera_combo['values'] = [cam['index'] for cam in self.cameras]
        
    def create_warning_window(self):
        """Create a full-screen warning overlay"""
        if self.warning_window:
            return
            
        self.warning_window = tk.Toplevel()
        self.warning_window.attributes('-fullscreen', True)
        self.warning_window.attributes('-topmost', True)
        self.warning_window.configure(bg='black')
        
        # Add warning text
        warning_label = tk.Label(
            self.warning_window,
            text=str(self.warnings_count),
            font=("Arial", 144, "bold"),
            bg='black',
            fg='white'
        )
        warning_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Make window click-through (doesn't block other applications)
        self.warning_window.overrideredirect(False)
        
    def destroy_warning_window(self):
        """Remove the warning overlay"""
        if self.warning_window:
            self.warning_window.destroy()
            self.warning_window = None
            
    def is_hand_in_danger_zone(self, hand_landmarks, frame_shape) -> bool:
        """Check if hand is in the danger zone (near face area)"""
        h, w = frame_shape[:2]
        
        # Get hand bounding box
        x_coords = [lm.x for lm in hand_landmarks.landmark]
        y_coords = [lm.y for lm in hand_landmarks.landmark]
        
        min_y = min(y_coords)
        max_y = max(y_coords)
        
        # Check if hand intersects with danger zone
        danger_top = self.danger_top_var.get()
        danger_bottom = self.danger_bottom_var.get()
        
        return (min_y < danger_bottom) and (max_y > danger_top)
    
    def process_frame(self, frame):
        """Process a single frame for hand detection"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        hands_in_danger = False
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks on frame
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Check if hand is in danger zone
                if self.is_hand_in_danger_zone(hand_landmarks, frame.shape):
                    hands_in_danger = True
                    
                    # Draw danger zone indicator
                    h, w = frame.shape[:2]
                    cv2.rectangle(frame, 
                                (0, int(h * self.danger_top_var.get())), 
                                (w, int(h * self.danger_bottom_var.get())), 
                                (0, 0, 255), 3)
        
        # Update warning state
        current_time = time.time()
        if current_time - self.last_warning_update > self.warning_cooldown:
            if hands_in_danger and not self.warning_active:
                self.activate_warning()
            elif not hands_in_danger and self.warning_active:
                self.deactivate_warning()
            self.last_warning_update = current_time
            
        return frame
    
    def activate_warning(self):
        """Activate the warning system"""
        if not self.warning_active:
            self.warning_active = True
            self.warnings_count += 1
            self.warnings_count_var.set(f"Warnings triggered: {self.warnings_count}")
            self.root.after(0, self.create_warning_window)
            
    def deactivate_warning(self):
        """Deactivate the warning system"""
        if self.warning_active:
            self.warning_active = False
            self.root.after(0, self.destroy_warning_window)
    
    def update_session_time(self):
        """Update the session time display"""
        if self.session_start_time and self.running:
            elapsed = time.time() - self.session_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.session_time_var.set(f"Session time: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
        if self.running:
            self.root.after(1000, self.update_session_time)
    
    def start_monitoring(self):
        """Start the hand monitoring system"""
        try:
            # Get selected camera index
            selected_camera = self.selected_camera_var.get()
            
            if not self.cameras:
                raise Exception("No cameras available. Please refresh and try again.")
            
            # Find camera info for selected camera
            camera_info = next((cam for cam in self.cameras if cam['index'] == selected_camera), None)
            if not camera_info:
                raise Exception(f"Selected camera {selected_camera} is not available.")
            
            # Try to open the selected camera
            self.cap = cv2.VideoCapture(selected_camera)
            if not self.cap.isOpened():
                raise Exception(f"Could not open camera {selected_camera}")
            
            # Test if we can read a frame
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                self.cap.release()
                raise Exception(f"Camera {selected_camera} opened but cannot read frames")
            
            self.current_camera_index = selected_camera
            self.running = True
            self.session_start_time = time.time()
            self.warnings_count = 0
            self.warnings_count_var.set("Warnings triggered: 0")
            
            camera_type = "External" if camera_info['is_external'] else "Integrated"
            self.status_label.config(text=f"Status: Monitoring Active (Camera {selected_camera})")
            self.camera_status_var.set(f"Camera: {camera_info['name']} ({camera_type})")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Start the monitoring thread
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            # Start session time updates
            self.update_session_time()
            
            print(f"Started monitoring with {camera_type.lower()} camera: {camera_info['name']}")
            
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            print(f"Camera error: {e}")
    
    def stop_monitoring(self):
        """Stop the hand monitoring system"""
        self.running = False
        
        if self.cap:
            self.cap.release()
            
        cv2.destroyAllWindows()
        self.deactivate_warning()
        
        self.status_label.config(text="Status: Stopped")
        self.camera_status_var.set("Camera: Not active")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.current_camera_index = None
    
    def monitor_loop(self):
        """Main monitoring loop (runs in separate thread)"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame from camera")
                break
                
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Process frame for hand detection
            processed_frame = self.process_frame(frame)
            
            # Show the frame (optional - for debugging)
            cv2.imshow(f'Hand Detection - Camera {self.current_camera_index} (Press Q to close)', processed_frame)
            
            # Break on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.root.after(0, self.stop_monitoring)
    
    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def on_closing(self):
        """Handle application closing"""
        self.stop_monitoring()
        self.root.destroy()

if __name__ == "__main__":
    # Check if required packages are available
    try:
        import cv2
        import mediapipe as mp
    except ImportError as e:
        print("Missing required packages. Please install with:")
        print("pip install opencv-python mediapipe")
        exit(1)
    
    # Set environment variables for better Docker compatibility
    import os
    os.environ['OPENCV_VIDEOIO_PRIORITY_V4L2'] = '1'
    os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'  # Reduce OpenCV log spam
    
    # Disable MediaPipe GPU acceleration (fixes OpenGL errors in Docker)
    os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'
    
    print("TrichShot")
    print("This app will monitor your hands and warn when they get near your face.")
    print("External cameras are automatically prioritized over integrated cameras.")
    print("Press 'Start Monitoring' to begin, and 'q' in the video window to stop.")
    print("Adjust the danger zone sliders to customize the detection area.\n")
    
    app = TrichShotApp()
    app.run()