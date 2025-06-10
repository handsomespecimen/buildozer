from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import NumericProperty
import random
import math
from ursina import *

# Initialize ursina in a way that works with Kivy
class UrsinaWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ursina_app = Ursina()
        self.ursina_app.disable_input()  # We'll handle input through Kivy
        
        # Create dice entity
        self.dice = Entity(
            model='cube',
            texture='white_cube',
            color=color.white,
            scale=0.5,
            position=(0, 0, 0),
            collider='box'
        )
        
        # Add numbers to dice faces
        self.dice_numbers = []
        for i in range(6):
            number = Text(
                text=str(i+1),
                scale=0.2,
                parent=self.dice,
                position=(0, 0, 0.51),
                rotation=(0, 0, 0),
                color=color.black
            )
            self.dice_numbers.append(number)
        
        # Position numbers on each face
        self.dice_numbers[0].world_position = self.dice.world_position + Vec3(0, 0, 0.51)
        self.dice_numbers[1].world_position = self.dice.world_position + Vec3(0, 0, -0.51)
        self.dice_numbers[2].world_position = self.dice.world_position + Vec3(0, 0.51, 0)
        self.dice_numbers[2].world_rotation = (90, 0, 0)
        self.dice_numbers[3].world_position = self.dice.world_position + Vec3(0, -0.51, 0)
        self.dice_numbers[3].world_rotation = (90, 0, 0)
        self.dice_numbers[4].world_position = self.dice.world_position + Vec3(0.51, 0, 0)
        self.dice_numbers[4].world_rotation = (0, 90, 0)
        self.dice_numbers[5].world_position = self.dice.world_position + Vec3(-0.51, 0, 0)
        self.dice_numbers[5].world_rotation = (0, 90, 0)
        
        # Physics setup
        self.dice.physics = RigidBody(
            mass=1,
            friction=0.5,
            restitution=0.3  # bounciness
        )
        self.dice.physics.add_force(Vec3(0, 0, 0))  # Start with no force
        
        # Ground plane
        self.ground = Entity(
            model='plane',
            texture='white_cube',
            color=color.gray,
            scale=10,
            position=(0, -1, 0),
            collider='box'
        )
        
        # Walls to keep dice in view
        self.walls = [
            Entity(model='cube', scale=(10, 2, 0.1), position=(0, 0, -2), collider='box', color=color.clear),
            Entity(model='cube', scale=(10, 2, 0.1), position=(0, 0, 2), collider='box', color=color.clear),
            Entity(model='cube', scale=(0.1, 2, 10), position=(-2, 0, 0), collider='box', color=color.clear),
            Entity(model='cube', scale=(0.1, 2, 10), position=(2, 0, 0), collider='box', color=color.clear)
        ]
        
        # Camera setup
        camera.position = (0, 2, -4)
        camera.rotation = (20, 0, 0)
        
        # Result display
        self.result_text = Text(
            text='Shake to roll!',
            position=(-0.8, 0.4),
            scale=2,
            color=color.black
        )
        
        # Variables
        self.is_rolling = False
        self.last_shake_time = 0
        self.last_acceleration = 0
        
        # Schedule ursina update
        Clock.schedule_interval(self.update_ursina, 1/60.)
    
    def update_ursina(self, dt):
        # Update ursina engine
        self.ursina_app.step()
        
        # Check if dice has stopped moving
        if self.is_rolling and self.dice.physics.velocity.length() < 0.01:
            self.is_rolling = False
            self.show_result()
    
    def roll_dice(self, intensity=1.0):
        self.is_rolling = True
        self.result_text.text = ''
        
        # Apply random force and torque
        force = Vec3(
            random.uniform(-5, 5) * intensity,
            random.uniform(2, 5) * intensity,
            random.uniform(-5, 5) * intensity
        )
        
        torque = Vec3(
            random.uniform(-50, 50) * intensity,
            random.uniform(-50, 50) * intensity,
            random.uniform(-50, 50) * intensity
        )
        
        self.dice.physics.velocity = Vec3(0, 0, 0)
        self.dice.physics.angular_velocity = Vec3(0, 0, 0)
        self.dice.position = (0, 0.5, 0)
        self.dice.rotation = (0, 0, 0)
        self.dice.physics.add_force(force)
        self.dice.physics.add_torque(torque)
    
    def show_result(self):
        # Determine which face is up
        up = Vec3(0, 1, 0)
        best_dot = -1
        result = 1
        
        # Check each face normal
        faces = [
            Vec3(0, 0, 1),   # front (1)
            Vec3(0, 0, -1),  # back (2)
            Vec3(0, 1, 0),   # top (3)
            Vec3(0, -1, 0),  # bottom (4)
            Vec3(1, 0, 0),   # right (5)
            Vec3(-1, 0, 0)    # left (6)
        ]
        
        for i, normal in enumerate(faces):
            # Transform normal by dice rotation
            rotated_normal = self.dice.world_rotation * normal
            dot = rotated_normal.dot(up)
            if dot > best_dot:
                best_dot = dot
                result = i + 1
        
        self.result_text.text = f'Result: {result}'
    
    def on_touch_down(self, touch):
        # Alternative way to roll by tapping
        self.roll_dice(intensity=1.0)
        return True

class DiceRollerApp(App):
    def build(self):
        # Setup accelerometer if available
        try:
            from plyer import accelerometer
            accelerometer.enable()
            Clock.schedule_interval(self.check_shake, 1.0 / 60.0)
        except:
            print("Accelerometer not available")
        
        self.ursina_widget = UrsinaWidget()
        return self.ursina_widget
    
    def check_shake(self, dt):
        try:
            from plyer import accelerometer
            accel = accelerometer.acceleration
            
            if accel is not None:
                x, y, z = accel[0] or 0, accel[1] or 0, accel[2] or 0
                acceleration = math.sqrt(x*x + y*y + z*z)
                
                # Detect sudden acceleration changes
                if acceleration > 15 and not self.ursina_widget.is_rolling:
                    self.ursina_widget.roll_dice(intensity=acceleration/15)
        except:
            pass

if __name__ == '__main__':
    Window.clearcolor = (0.9, 0.9, 0.9, 1)
    DiceRollerApp().run()
