from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.clock import Clock
from plyer import gps, accelerometer, gyroscope, compass
import math
import numpy as np
from datetime import datetime
from android.permissions import request_permissions, Permission

class SensorFusion:
    def __init__(self):
        self.velocity = np.zeros(3)  # [x, y, z] in m/s
        self.position = np.zeros(3)  # [lat, lon, alt] in degrees/meters
        self.orientation = np.zeros(3)  # [roll, pitch, yaw] in radians
        self.last_gps = None
        self.last_update = datetime.now()
        self.gps_interval = 10.0  # seconds between GPS updates
        self.alpha = 0.98  # complementary filter constant
        
    def update(self, accel, gyro, compass_data, gps_data=None):
        now = datetime.now()
        dt = (now - self.last_update).total_seconds()
        self.last_update = now
        
        # Update orientation using complementary filter
        self.orientation += gyro * dt
        if compass_data:
            self.orientation[2] = self.alpha * (self.orientation[2] + gyro[2] * dt) + \
                                (1 - self.alpha) * math.radians(compass_data[0])
        
        # Transform acceleration to world coordinates
        accel_world = self.rotate_vector(accel, self.orientation)
        accel_world[2] -= 9.81  # Remove gravity
        
        # Update velocity and position
        self.velocity += accel_world * dt
        
        if gps_data and (self.last_gps is None or 
                        (now - self.last_gps).total_seconds() >= self.gps_interval):
            self.position = np.array([gps_data['lat'], gps_data['lon'], gps_data['alt']])
            self.velocity = np.zeros(3)  # Reset velocity on GPS update
            self.last_gps = now
        else:
            # Dead reckoning between GPS updates
            delta_pos = self.velocity * dt
            self.position[0] += delta_pos[0] / 111111.0  # approx lat degrees
            self.position[1] += delta_pos[1] / (111111.0 * math.cos(math.radians(self.position[0])))
            self.position[2] += delta_pos[2]
    
    def rotate_vector(self, v, orientation):
        # Simplified rotation (proper implementation would use rotation matrices)
        yaw = orientation[2]
        return np.array([
            v[0] * math.cos(yaw) - v[1] * math.sin(yaw),
            v[0] * math.sin(yaw) + v[1] * math.cos(yaw),
            v[2]
        ])

class EfficientBreadcrumbsApp(App):
    def build(self):
        request_permissions([
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION
        ])
        
        self.sensor_fusion = SensorFusion()
        self.waypoints = []
        self.tracking = False
        self.last_drawn = []
        
        # Setup UI
        layout = BoxLayout(orientation='vertical')
        self.ar_view = Label(size_hint=(1, 0.7))
        layout.add_widget(self.ar_view)
        
        controls = BoxLayout(size_hint=(1, 0.3))
        self.toggle_btn = ToggleButton(text="Start Tracking")
        self.toggle_btn.bind(on_press=self.toggle_tracking)
        controls.add_widget(self.toggle_btn)
        
        self.gps_status = Label(text="GPS: Off")
        controls.add_widget(self.gps_status)
        layout.add_widget(controls)
        
        # Sensor setup
        self.setup_sensors()
        Clock.schedule_interval(self.update_display, 0.05)
        
        return layout
    
    def setup_sensors(self):
        try:
            # Configure minimal GPS
            gps.configure(on_location=self.on_gps)
            gps.start(minTime=10000, minDistance=10)  # 10 second/10 meter minimum
            
            # Enable high-frequency sensors
            accelerometer.enable()
            gyroscope.enable()
            compass.enable()
            
            Clock.schedule_interval(self.update_sensors, 0.1)
        except Exception as e:
            print(f"Sensor error: {e}")
    
    def on_gps(self, **kwargs):
        self.sensor_fusion.update(
            accel=np.zeros(3),  # Will be updated by sensor thread
            gyro=np.zeros(3),
            compass_data=None,
            gps_data={
                'lat': kwargs.get('lat', 0),
                'lon': kwargs.get('lon', 0),
                'alt': kwargs.get('altitude', 0)
            }
        )
        self.gps_status.text = f"GPS: {kwargs.get('accuracy', 0):.1f}m"
    
    def update_sensors(self, dt):
        try:
            accel = np.array(accelerometer.acceleration[:3])
            gyro = np.array([math.radians(g) for g in gyroscope.orientation[:3]])
            compass_data = compass.orientation
            
            self.sensor_fusion.update(
                accel=accel,
                gyro=gyro,
                compass_data=compass_data
            )
        except:
            pass
    
    def toggle_tracking(self, instance):
        self.tracking = not instance.state == 'down'
        instance.text = "Stop Tracking" if self.tracking else "Start Tracking"
        
        if self.tracking:
            self.record_breadcrumb()
            Clock.schedule_interval(self.record_breadcrumb, 5.0)  # Less frequent recording
        else:
            Clock.unschedule(self.record_breadcrumb)
    
    def record_breadcrumb(self, dt=None):
        pos = self.sensor_fusion.position
        self.last_drawn.append({
            'lat': pos[0],
            'lon': pos[1],
            'alt': pos[2],
            'time': datetime.now().isoformat()
        })
    
    def update_display(self, dt):
        self.ar_view.canvas.clear()
        
        # Get current position from sensor fusion
        current_pos = self.sensor_fusion.position
        orientation = self.sensor_fusion.orientation[2]  # yaw
        
        # Draw waypoints
        for wp in self.waypoints:
            self.draw_waypoint(wp, current_pos, orientation)
        
        # Draw breadcrumbs
        if len(self.last_drawn) > 1:
            points = []
            for crumb in self.last_drawn[-20:]:  # Limit to 20 points
                x, y = self.calculate_screen_pos(
                    current_pos[:2], 
                    [crumb['lat'], crumb['lon']],
                    orientation
                )
                points.extend([x, y])
            
            with self.ar_view.canvas:
                Color(0, 1, 0, 0.7)
                Line(points=points, width=2)
    
    def draw_waypoint(self, waypoint, current_pos, orientation):
        x, y = self.calculate_screen_pos(
            current_pos[:2],
            [waypoint['lat'], waypoint['lon']],
            orientation
        )
        
        distance = self.calculate_distance(current_pos[:2], [waypoint['lat'], waypoint['lon']])
        
        with self.ar_view.canvas:
            Color(1, 0, 0)
            Ellipse(pos=(x-10, y-10), size=(20, 20))
            Color(1, 1, 1)
            Rectangle(pos=(x-30, y+15), size=(60, 20))
            Color(0, 0, 0)
            Label(text=f"{distance:.1f}m", pos=(x-30, y+15), size=(60, 20))
    
    def calculate_screen_pos(self, pos1, pos2, heading):
        # Simplified projection - would use proper AR math in production
        bearing = self.calculate_bearing(pos1, pos2)
        rel_angle = (bearing - math.degrees(heading) + 360) % 360
        distance = self.calculate_distance(pos1, pos2)
        
        center_x, center_y = self.ar_view.center
        angle_rad = math.radians(rel_angle)
        scale = min(1000/distance, 1)
        
        return (
            center_x + math.cos(angle_rad) * 200 * scale,
            center_y + math.sin(angle_rad) * 200 * scale
        )
    
    def calculate_bearing(self, pos1, pos2):
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        return (math.degrees(math.atan2(y, x)) + 360) % 360
    
    def calculate_distance(self, pos1, pos2):
        # Haversine formula
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

if __name__ == '__main__':
    EfficientBreadcrumbsApp().run()
