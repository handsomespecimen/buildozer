from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from android.permissions import request_permissions, Permission
import cv2
import numpy as np
import time
from plyer import notification

class FaceDistanceDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.known_width = 14.0  # Average face width in cm
        self.focal_length = 700   # Approximate focal length (needs calibration)
        self.min_distance_cm = 40  # Minimum recommended distance
        self.last_notification_time = 0
        self.notification_cooldown = 30  # seconds
        
    def detect_face_distance(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # Calculate distance
            distance = (self.known_width * self.focal_length) / w
            return distance
            
        return None

class FaceDistanceApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.detector = FaceDistanceDetector()
        self.capture = None
        self.is_running = False
        self.background_service = False

    def build(self):
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        self.status_label = Label(text="Face Distance Monitor", font_size='20sp')
        self.distance_label = Label(text="Distance: -- cm", font_size='18sp')
        self.warning_label = Label(text="", color=(1, 0, 0, 1))
        
        self.toggle_btn = Button(text="Start Monitoring", size_hint=(1, 0.2))
        self.toggle_btn.bind(on_press=self.toggle_monitoring)
        
        self.background_switch = Switch(active=self.background_service)
        self.background_switch.bind(active=self.toggle_background_service)
        background_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        background_layout.add_widget(Label(text="Run in background:"))
        background_layout.add_widget(self.background_switch)
        
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.distance_label)
        self.layout.add_widget(self.warning_label)
        self.layout.add_widget(background_layout)
        self.layout.add_widget(self.toggle_btn)
        
        if platform == 'android':
            request_permissions([Permission.CAMERA, Permission.WAKE_LOCK])
            
        return self.layout

    def toggle_monitoring(self, instance):
        if self.is_running:
            self.stop_monitoring()
            self.toggle_btn.text = "Start Monitoring"
        else:
            self.start_monitoring()
            self.toggle_btn.text = "Stop Monitoring"

    def toggle_background_service(self, instance, value):
        self.background_service = value

    def start_monitoring(self):
        self.capture = cv2.VideoCapture(0)
        self.is_running = True
        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS

    def stop_monitoring(self):
        if self.capture:
            self.capture.release()
            self.capture = None
        self.is_running = False
        Clock.unschedule(self.update_frame)
        self.distance_label.text = "Distance: -- cm"
        self.warning_label.text = ""

    def update_frame(self, dt):
        ret, frame = self.capture.read()
        if ret:
            distance = self.detector.detect_face_distance(frame)
            
            if distance is not None:
                self.distance_label.text = f"Distance: {distance:.1f} cm"
                
                if distance < self.detector.min_distance_cm:
                    self.warning_label.text = "TOO CLOSE! Move back!"
                    current_time = time.time()
                    if (current_time - self.detector.last_notification_time) > self.detector.notification_cooldown:
                        self.show_notification(distance)
                        self.detector.last_notification_time = current_time
                else:
                    self.warning_label.text = ""
            else:
                self.distance_label.text = "Distance: No face detected"
                self.warning_label.text = ""

    def show_notification(self, distance):
        if platform == 'android':
            notification.notify(
                title="Too Close to Screen!",
                message=f"You're only {distance:.1f} cm away. Move back to at least {self.detector.min_distance_cm} cm.",
                app_name="Face Distance Alert",
                timeout=10
            )

    def on_pause(self):
        if self.background_service and self.is_running:
            return True
        return False

    def on_resume(self):
        if self.background_service and self.is_running and not self.capture:
            self.start_monitoring()

if __name__ == '__main__':
    FaceDistanceApp().run()
