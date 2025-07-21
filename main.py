from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
import pyttsx3

class Keypad(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.code_input = ''
        self.valid_codes = {
            '1234': ('ALPHA', self.protocol_alpha),
            '5678': ('BETA', self.protocol_beta)
        }
        self.engine = pyttsx3.init()

        self.display = Label(text='Enter Code', font_size=40, size_hint=(1, 0.3))
        self.add_widget(self.display)

        buttons_layout = BoxLayout()
        for i in range(1, 10):
            btn = Button(text=str(i), font_size=32)
            btn.bind(on_press=self.button_press)
            buttons_layout.add_widget(btn)
            if i % 3 == 0:
                self.add_widget(buttons_layout)
                buttons_layout = BoxLayout()
        btn_zero = Button(text='0', font_size=32)
        btn_zero.bind(on_press=self.button_press)
        buttons_layout.add_widget(btn_zero)
        btn_clear = Button(text='Clear', font_size=32)
        btn_clear.bind(on_press=self.clear_code)
        buttons_layout.add_widget(btn_clear)
        btn_enter = Button(text='Enter', font_size=32)
        btn_enter.bind(on_press=self.check_code)
        buttons_layout.add_widget(btn_enter)
        self.add_widget(buttons_layout)

    def button_press(self, instance):
        if len(self.code_input) < 8:
            self.code_input += instance.text
            self.display.text = '*' * len(self.code_input)

    def clear_code(self, instance):
        self.code_input = ''
        self.display.text = 'Enter Code'

    def check_code(self, instance):
        if self.code_input in self.valid_codes:
            name, func = self.valid_codes[self.code_input]
            msg = f"PROTOCOL {name} INITIATED"
            self.display.text = msg
            self.speak(msg)
            func()
        else:
            self.display.text = "INVALID CODE"
            self.speak("Invalid code")
        self.code_input = ''

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def protocol_alpha(self):
        print("Alpha protocol running preset action")

    def protocol_beta(self):
        print("Beta protocol running preset action")

class KeypadApp(App):
    def build(self):
        return Keypad()

if __name__ == '__main__':
    KeypadApp().run()