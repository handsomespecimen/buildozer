from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from jnius import autoclass

# theoretical Android sensors
theoretical_sensors = {
    "TYPE_ACCELEROMETER": 1,
    "TYPE_ACCELEROMETER_UNCALIBRATED": 35,
    "TYPE_GRAVITY": 9,
    "TYPE_LINEAR_ACCELERATION": 10,
    "TYPE_GYROSCOPE": 4,
    "TYPE_GYROSCOPE_UNCALIBRATED": 16,
    "TYPE_ROTATION_VECTOR": 11,
    "TYPE_GAME_ROTATION_VECTOR": 15,
    "TYPE_GEOMAGNETIC_ROTATION_VECTOR": 20,
    "TYPE_SIGNIFICANT_MOTION": 17,
    "TYPE_STEP_DETECTOR": 18,
    "TYPE_STEP_COUNTER": 19,
    "TYPE_AMBIENT_TEMPERATURE": 13,
    "TYPE_PRESSURE": 6,
    "TYPE_RELATIVE_HUMIDITY": 12,
    "TYPE_LIGHT": 5,
    "TYPE_PROXIMITY": 8,
    "TYPE_MAGNETIC_FIELD": 2,
    "TYPE_MAGNETIC_FIELD_UNCALIBRATED": 14,
    "TYPE_ORIENTATION": 3,
    "TYPE_POSE_6DOF": 28,
    "TYPE_HEART_RATE": 21,
    "TYPE_HEART_BEAT": 31,
    "TYPE_LOW_LATENCY_OFFBODY_DETECT": 34,
    "TYPE_DEVICE_PRIVATE_BASE": 65536,
    "TYPE_MOTION_DETECT": 30,
    "TYPE_STATIONARY_DETECT": 29,
    "TYPE_PICK_UP_GESTURE": 25,
    "TYPE_WRIST_TILT_GESTURE": 26,
    "TYPE_WAKE_GESTURE": 23,
    "TYPE_GLANCE_GESTURE": 24,
    "TYPE_TILT_DETECTOR": 22,
    "TYPE_HINGE_ANGLE": 36,
    "TYPE_TEMPERATURE": 7
}

class SensorCheckApp(App):
    def build(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        Sensor = autoclass('android.hardware.Sensor')
        SensorManager = autoclass('android.hardware.SensorManager')

        activity = PythonActivity.mActivity
        sm = activity.getSystemService(Context.SENSOR_SERVICE)

        phone_sensors = {}
        sensor_list = sm.getSensorList(Sensor.TYPE_ALL)
        for s in sensor_list.toArray():
            phone_sensors[s.getName()] = s.getType()

        # compare
        have = []
        missing = []
        extra = []

        for name, stype in theoretical_sensors.items():
            if stype in phone_sensors.values():
                have.append(name)
            else:
                missing.append(name)

        for pname, ptype in phone_sensors.items():
            if ptype not in theoretical_sensors.values():
                extra.append(f"{pname} (type {ptype})")

        # prepare scrollable text
        text = "=== SENSORS PRESENT ===\n" + "\n".join(have)
        text += "\n\n=== SENSORS MISSING ===\n" + "\n".join(missing)
        text += "\n\n=== EXTRA SENSORS (vendor-specific) ===\n" + "\n".join(extra)

        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView()
        label = Label(text=text, size_hint_y=None, markup=True)
        label.bind(texture_size=lambda instance, value: setattr(label, 'height', value[1]))
        scroll.add_widget(label)
        layout.add_widget(scroll)
        return layout

if __name__ == '__main__':
    SensorCheckApp().run()