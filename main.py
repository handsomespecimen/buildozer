import os
import math
import random
import threading
import time
import multiprocessing
import wave
import struct
import tempfile

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from jnius import autoclass

os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")
os.environ.setdefault("KIVY_GL_BACKEND", "sdl2")
Config.set("graphics", "width",  "450")
Config.set("graphics", "height", "900")
Config.set("graphics", "resizable", "0")

def speakf(text):
    tts = autoclass("android.speech.tts.TextToSpeech")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    act = PythonActivity.mActivity
    tts_obj = tts(act, None)
    tts_obj.setSpeechRate(0.6)
    tts_obj.setPitch(0.3)
    tts_obj.speak(txt, tts_obj.QUEUE_FLUSH, None)

NUM_BARS   = 9
LERP_SPEED = 0.16

VOWELS     = set("AEIOU")
PLOSIVES   = set("BPDTGK")
SIBILANTS  = set("SZ")
NASALS     = set("MNL")

LCD_GREEN_ON      = (0.50, 0.72, 0.18, 1)
LCD_GREEN_OFF     = (0.12, 0.18, 0.05, 1)
LCD_TEXT_ON       = (0.06, 0.10, 0.02, 1)
LCD_TEXT_OFF      = (0.20, 0.28, 0.10, 1)
LCD_BORDER_ON     = (0.35, 0.52, 0.10, 1)
LCD_BORDER_OFF    = (0.15, 0.20, 0.08, 1)

CHASSIS_TOP       = (0.13, 0.13, 0.14, 1)
CHASSIS_EDGE      = (0.19, 0.19, 0.21, 1)

SCREW_BODY        = (0.22, 0.22, 0.24, 1)
SCREW_SLOT        = (0.30, 0.30, 0.33, 1)

PWR_RING_OFF      = (0.50, 0.10, 0.10, 1)
PWR_RING_ON       = (0.18, 0.80, 0.28, 1)
PWR_ICON_OFF      = (0.80, 0.18, 0.18, 1)
PWR_ICON_ON       = (0.28, 1.00, 0.45, 1)
PWR_BG_OFF        = (0.10, 0.06, 0.06, 1)
PWR_BG_ON         = (0.06, 0.12, 0.07, 1)

QUERY_BG          = (0.11, 0.11, 0.13, 1)
QUERY_EDGE        = (0.20, 0.20, 0.23, 1)
QUERY_ACTIVE_BG   = (0.18, 0.18, 0.22, 1)
QUERY_ACTIVE_EDGE = (0.35, 0.35, 0.45, 1)
QUERY_TEXT        = (0.60, 0.65, 0.58, 1)
QUERY_TEXT_ACT    = (0.82, 0.88, 0.78, 1)
QUERY_DIS_BG      = (0.09, 0.09, 0.10, 1)
QUERY_DIS_EDGE    = (0.13, 0.13, 0.15, 1)
QUERY_DIS_TEXT    = (0.28, 0.30, 0.26, 1)

SMALL_FONT     = sp(10)
NORMAL_FONT    = sp(11.5)
NORMALISH_FONT = sp(13)
COMMON_FONT    = sp(13)
DECENT_FONT    = sp(15)
DECENTER_FONT  = sp(16)
BIG_FONT       = sp(20)

GHOST_RESPONSES = {
    "location": [
        "BEHIND YOU", "IN THE WALLS", "BENEATH YOUR FEET",
        "ABOVE", "HERE", "EVERYWHERE", "THE CORNER",
        "FOLLOW THE COLD", "BELOW THE STAIRS", "WHERE YOU SLEEP", "SO CLOSE",
        "INSIDE THE FLOORBOARDS", "IN THE DARK HALL", "UNDER YOUR BED",
        "IN THE CEILING SPACE", "JUST OUT OF SIGHT", "IN THE MIRROR",
        "NEXT ROOM", "OUTSIDE YOUR WINDOW", "IN YOUR SHADOW",
        "WHERE LIGHT DOESN'T REACH", "IN THE DOORWAY", "BEHIND THE CURTAIN",
        "IN THE BASEMENT", "AT YOUR BACK", "ON THE ROOF",
        "IN THE STATIC", "IN THE SILENCE", "IN THE HALLWAY",
        "UNDER THE STAIRS", "IN THE ATTIC", "IN THE FLOOR BELOW",
        "IN THE VOID CORNER", "IN THE ECHO", "IN THE COLD SPOT",
        "IN THE DOOR FRAME", "IN THE DARK WATER", "IN THE LAMP LIGHT",
        "JUST BEYOND YOU", "IN YOUR PERIPHERY", "IN THE EMPTY ROOM",
        "WHERE YOU TURNED AWAY", "IN THE CLOSED SPACE", "IN THE DARK REFLECTION"
    ],
    "death": [
        "THE FIRE", "THEY DROWNED ME", "BETRAYED", "ALONE",
        "SLOWLY", "I DIDN'T SUFFER", "THE FALL", "A LIE",
        "BY THEIR HANDS", "COLD WATER", "NO ONE CAME", "QUICKLY",
        "BURNED IN SILENCE", "BURIED ALIVE", "LOST IN SMOKE",
        "THE KNIFE DID NOT STOP", "THE HOUSE DID IT", "NO AIR LEFT",
        "THE DOOR CLOSED", "FELL WITHOUT END", "SOMETHING PUSHED ME",
        "THE LIGHT WENT OUT", "I WAS FORGOTTEN", "THE RIVER TOOK ME",
        "THE WALLS CLOSED IN", "THE CHAIR BROKE", "THE ROPE HELD",
        "THEY LEFT ME THERE", "FROZEN MIDBREATH", "THE GROUND OPENED",
        "THE SOUND STOPPED", "NO LAST WORD", "THE SHADOW STRUCK",
        "THE NIGHT DID IT", "I NEVER LEFT", "IT WAS INSIDE ME"
    ],
    "age": [
        "OLDER THAN YOU THINK", "YOUNG", "THIRTY-THREE",
        "A CHILD", "ANCIENT", "DOES IT MATTER", "FORGOTTEN",
        "TIME MEANS NOTHING HERE", "OLDER THAN THIS HOUSE",
        "BEFORE RECORDS", "BEYOND YEARS", "NO LONGER COUNTED",
        "FROZEN IN ONE MOMENT", "BEFORE YOU WERE BORN",
        "AFTER EVERYTHING", "I STOPPED AGING HERE",
        "AGELESS NOW", "LOST IN TIME", "OLDER THAN THE WOOD",
        "OLDER THAN THE STONE", "I WAS NEVER BORN",
        "TIME SKIPPED ME", "INFINITE", "UNCOUNTED",
        "PAST MEMORY", "NO LONGER HUMAN TIME",
        "I EXIST BETWEEN YEARS", "TIME FORGOT ME"
    ],
    "name": [
        "MARGARET", "ELIAS", "THOMAS", "NO NAME NOW",
        "WHISPER IT", "FORGOTTEN", "NEVER TELL",
        "CALL ME SHADOW", "ALICE", "ONCE I HAD ONE",
        "DAVID", "JULIA", "HENRY", "LUCAS", "SARAH",
        "THE ONE WHO STAYED", "I DON'T USE IT",
        "SPOKEN ONLY ONCE", "UNKNOWN", "REDACTED",
        "THE OLD NAME", "BROKEN NAME", "ECHO OF A NAME",
        "STILL HERE BUT NOT NAMED", "CALL ME ANYTHING",
        "IT DOESN'T WORK ANYMORE", "NAMELESS VOICE",
        "I ERASED IT", "NO ONE SAYS IT NOW"
    ],
    "sign": [
        "COLD", "WATCHING", "FEEL THE BREEZE", "THE LIGHTS",
        "LOOK BEHIND", "THE MIRROR", "YOU ALREADY KNOW",
        "THREE KNOCKS", "STATIC", "NOT ALONE",
        "DOOR MOVES ITSELF", "LIGHT FLICKERS TWICE",
        "SHADOWS SHIFT WRONG", "TEMPERATURE DROPS",
        "FOOTSTEPS ABOVE", "WHISPER IN EMPTY ROOM",
        "GLASS VIBRATES", "RADIO SPEAKS BACK",
        "CLOCK STOPS", "WINDOW BREATHES",
        "PAINT DRIPS BACKWARD", "CHAIR SCRAPES",
        "HUM IN WALLS", "LIGHT WON'T STAY ON",
        "DOOR HANDLE TURNS SLOWLY", "REFLECTION LAGS",
        "SOMETHING BLINKS WHEN YOU DON'T", "BREATH ON NECK"
    ],
    "presence": [
        "MANY OF US", "JUST ME", "WE ARE LEGION",
        "COUNT THE SHADOWS", "MORE THAN YOU SEE",
        "YOU BROUGHT US HERE", "LEAVE NOW", "DOZENS",
        "WE NEVER LEFT", "WE ARE STILL HERE",
        "TOO MANY TO NAME", "WE SHARE THIS SPACE",
        "YOU ADDED ANOTHER", "WE GROW IN SILENCE",
        "EVERY ROOM HOLDS ONE", "WE WATCH TOGETHER",
        "WE MOVE AS ONE", "WE WERE ALWAYS HERE",
        "WE DON'T SLEEP", "WE ARE IN THE WALLS",
        "WE FOLLOW YOU NOW", "WE WERE WAITING",
        "YOU ARE SURROUNDED", "WE DON'T END",
        "WE ARE BEHIND YOU STILL", "WE MULTIPLY IN DARKNESS"
    ],
    "message": [
        "GET OUT", "HELP ME", "DON'T LEAVE", "WARN THEM",
        "REMEMBER ME", "TELL HER", "STAY AWAY",
        "IT KNOWS YOU'RE HERE", "THEY LIED", "RUN",
        "DON'T LOOK BACK", "IT'S TOO LATE",
        "SAVE YOURSELF", "DON'T TRUST THEM",
        "OPEN THE DOOR", "CLOSE IT AGAIN",
        "I AM STILL HERE", "DON'T SLEEP HERE",
        "FREE ME", "STOP IT", "IT IS INSIDE",
        "DON'T SAY MY NAME", "LEAVE WHILE YOU CAN",
        "IT SEES YOU NOW", "DON'T COME BACK",
        "BURN THIS PLACE", "FORGET ME", "I AM NOT ALONE"
    ],
    "time": [
        "MIDNIGHT", "ALWAYS", "WHEN YOU'RE ALONE",
        "THREE AM", "NEVER ENDS", "SOON",
        "TIME IS BROKEN HERE", "EVERY NIGHT",
        "NO CLOCK WORKS", "TIME STANDS STILL",
        "AFTER MIDNIGHT", "BEFORE DAWN",
        "WHEN LIGHT DIES", "WHEN YOU BLINK",
        "BETWEEN SECONDS", "OUTSIDE TIME",
        "FOREVER STUCK", "LOST MINUTES",
        "NO MORNING COMES", "ENDLESS NIGHT",
        "REPEATING HOUR", "THE CLOCK LIES",
        "WHEN YOU STOP MOVING", "WHEN YOU FORGET",
        "TIME IS A ROOM HERE", "IT NEVER STARTED"
    ],
    "voice": [
        "SOFT WHISPER", "MULTIPLE VOICES", "A BREATH BEHIND WORDS",
        "STATIC SPEECH", "BROKEN LANGUAGE", "REPEATED PHRASE",
        "LOW HUM", "ECHO OF TALKING", "DISTANT SCREAM",
        "VOICE WITHOUT SOURCE", "INSIDE YOUR HEAD",
        "TWO PEOPLE AT ONCE", "UNDERLAPPING WORDS",
        "REVERSED SPEECH", "NOT HUMAN TIMBRE",
        "SOUND LIKE YOUR OWN", "GLITCHED VOICE",
        "WHISPERING WALLS", "VOICE IN METAL",
        "VOICE IN GLASS", "VOICE IN DARK AIR",
        "UNSPEAKABLE TONE", "NO MOUTH NEEDED",
        "VOICE THAT FADES WHEN LISTENED TO",
        "VOICE THAT ANSWERS BEFORE ASKED",
        "VOICE THAT DOESN'T MATCH LIPS"
    ],
    "fear": [
        "IT IS HERE", "DON'T MOVE", "IT SAW YOU",
        "BREATH STOPPED", "YOU SHOULDN'T BE HERE",
        "TURN OFF THE LIGHTS", "IT IS CLOSER",
        "SOMETHING BEHIND YOU IS WRONG",
        "DON'T SPEAK NOW", "IT HEARS FEAR",
        "YOU ARE NOT ALONE NOW", "RUN TOO LATE",
        "IT KNOWS YOUR NAME NOW", "IT LEARNED YOU",
        "DON'T LOOK AT IT", "IT IS LOOKING BACK",
        "YOU OPENED IT", "IT WOKE UP",
        "IT MOVES WHEN YOU BLINK",
        "YOUR SHADOW IS WRONG", "IT STOLE SILENCE",
        "YOU HEAR IT WRONG", "IT IS ALREADY INSIDE",
        "DON'T TRUST THE DARK", "IT BREATHES WHEN YOU DON'T"
    ],
    "place": [
        "THIS HOUSE", "THE HALLWAY", "THE ROOM YOU ENTERED",
        "THE FLOOR THAT CREAKS", "THE EMPTY BUILDING",
        "THE BASEMENT LEVEL", "THE TOP FLOOR",
        "THE STAIRCASE LOOP", "THE DOOR THAT LOCKS ITSELF",
        "THE WINDOWLESS ROOM", "THE HIDDEN CORRIDOR",
        "THE PLACE BEHIND WALLS", "THE LOST APARTMENT",
        "THE UNLISTED FLOOR", "THE BROKEN HOUSE",
        "THE SPACE BETWEEN ROOMS", "THE PLACE YOU MISSED",
        "THE BUILDING THAT REPEATS", "THE HOUSE THAT REMEMBERS",
        "THE EMPTY STREET", "THE ROOM THAT CHANGES",
        "THE HALL THAT EXTENDS", "THE CORNER THAT MOVES",
        "THE PLACE WITHOUT EXIT", "THE HOUSE THAT WATCHES",
        "THE PLACE YOU SHOULDN'T NAME"
    ],
    "warning": [
        "DON'T STAY", "LEAVE NOW", "IT IS TOO LATE",
        "TURN BACK", "DON'T ENTER", "DO NOT LISTEN",
        "CLOSE EVERYTHING", "LOCK THE DOOR",
        "DON'T RESPOND", "STOP TALKING",
        "DON'T USE LIGHT", "DON'T STAY ALONE",
        "DON'T COUNT THE SHADOWS",
        "IT REACTS TO YOU", "DON'T ACKNOWLEDGE IT",
        "DON'T REPEAT IT", "IGNORE THE SOUND",
        "DON'T FOLLOW IT", "DON'T GO UPSTAIRS",
        "DON'T GO DOWN", "DON'T TOUCH ANYTHING",
        "DON'T SLEEP HERE", "LEAVE THE HOUSE",
        "RUN BEFORE IT FINISHES"
    ]
}

JUMPSCARE_RESPONSES = [
    "I SEE YOU",
    "YOU ARE ALREADY DEAD",
    "I AM IN YOUR WALLS",
    "GET OUT. GET OUT NOW.",
    "YOU CANNOT ESCAPE ME",
    "WE ARE ALL AROUND YOU",
    "IT IS FAR TOO LATE",
    "I AM DIRECTLY BEHIND YOU",
    "YOUR SOUL IS MINE",
    "YOU SHOULD NOT HAVE SPOKEN",
    "I HAVE BEEN WATCHING YOU",
    "THE DARKNESS IS HUNGRY",
    "RUN. RUN NOW.",
    "YOU WOKE SOMETHING ANCIENT",
    "I WILL FOLLOW YOU HOME",
    "IT KNOWS YOUR FACE",
    "SCREAM. NO ONE WILL HEAR.",
    "YOU INVITED US IN",
    "WE HAVE ALWAYS BEEN HERE",
    "IT IS INSIDE YOU NOW",
]

QUESTIONS = {
    "Where are you?": "location",
    "How did you die?": "death",
    "How old are you?": "age",
    "What is your name?": "name",
    "Give us a sign.": "sign",
    "Are you alone?": "presence",
    "Do you have a message?": "message",
    "What time is it?": "time",
    "Can you hear us?": "sign",
    "Who are you?": "name",
    "Show yourself.": "sign",
    "What happened here?": "death",
    "Can you speak?": "voice",
    "What do you sound like?": "voice",
    "Who is there?": "presence",
    "Is anyone else here?": "presence",
    "What do you fear?": "fear",
    "Are we in danger?": "fear",
    "What is this place?": "place",
    "Where am i?": "place",
    "Should we leave?": "warning",
    "Is it safe?": "warning",
    "What should we do?": "warning",
    "Are you angry?": "message",
    "Do you want us gone?": "message",
    "Why are you here?": "presence",
    "Did something happen here?": "death",
    "How long has it been?": "time",
    "Is time broken?": "time"
}


def _generate_wav(duration, sample_rate, amplitude, envelope="flat"):
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        raw = random.randint(-amplitude, amplitude)
        if envelope == "attack":
            frac = i / num_samples
            gain = min(1.0, frac * 4.0)
            raw = int(raw * gain)
        elif envelope == "decay":
            frac = i / num_samples
            gain = max(0.0, 1.0 - frac)
            raw = int(raw * gain)
        elif envelope == "burst":
            frac = i / num_samples
            if frac < 0.05:
                gain = frac / 0.05
            elif frac > 0.80:
                gain = (1.0 - frac) / 0.20
            else:
                gain = 1.0
            raw = int(raw * gain)
        samples.append(max(-32768, min(32767, raw)))

    fname = os.path.join(tempfile.gettempdir(), f"sb_{envelope}_{duration}.wav")
    with wave.open(fname, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        data = struct.pack("<" + "h" * num_samples, *samples)
        f.writeframes(data)
    return fname


def _char_bar_profile(ch, amp):
    targets = []
    for i in range(NUM_BARS):
        frac = i / (NUM_BARS - 1)
        if ch in VOWELS:
            shape = 1.0 - 0.20 * abs(frac - 0.45)
            jitter = random.uniform(-0.06, 0.06)
        elif ch in PLOSIVES:
            shape = math.exp(-4.5 * (frac - 0.50) ** 2)
            jitter = random.uniform(-0.08, 0.08)
        elif ch in SIBILANTS:
            shape = 0.35 + 0.65 * frac
            jitter = random.uniform(-0.07, 0.07)
        elif ch in NASALS:
            shape = 0.75 - 0.20 * frac
            jitter = random.uniform(-0.05, 0.05)
        elif ch == ' ':
            targets.append(random.uniform(0.01, 0.04))
            continue
        else:
            shape = 0.85 - 0.35 * frac
            jitter = random.uniform(-0.07, 0.07)
        targets.append(max(0.02, min(0.98, amp * shape + jitter)))
    return targets

def build_phoneme_timeline(text, speech_rate=90):
    chars_per_sec = (speech_rate / 60.0) * 5.0
    timeline = []
    t = 0.0
    silence = [0.02] * NUM_BARS
    timeline.append((0.0, silence[:]))

    for ch in text.upper():
        if ch == ' ':
            dur = 1.0 / chars_per_sec * 2.5
            timeline.append((t + dur * 0.10, [random.uniform(0.01, 0.04) for _ in range(NUM_BARS)]))
            timeline.append((t + dur * 0.90, [random.uniform(0.01, 0.04) for _ in range(NUM_BARS)]))
            t += dur
            continue

        if ch in '.,!?\'"':
            dur = 1.0 / chars_per_sec * 3.5
            timeline.append((t + dur * 0.10, silence[:]))
            timeline.append((t + dur * 0.90, silence[:]))
            t += dur
            continue

        if ch in VOWELS:
            dur   = 1.0 / chars_per_sec * 1.6
            amp   = random.uniform(0.72, 0.97)
        elif ch in PLOSIVES:
            dur   = 1.0 / chars_per_sec * 0.85
            amp   = random.uniform(0.45, 0.72)
        elif ch in SIBILANTS:
            dur   = 1.0 / chars_per_sec * 1.1
            amp   = random.uniform(0.38, 0.62)
        elif ch in NASALS:
            dur   = 1.0 / chars_per_sec * 1.0
            amp   = random.uniform(0.30, 0.55)
        else:
            dur   = 1.0 / chars_per_sec * 0.95
            amp   = random.uniform(0.25, 0.52)

        peak_targets  = _char_bar_profile(ch, amp)
        onset_targets = [v * 0.45 for v in peak_targets]
        decay_targets = [v * 0.30 for v in peak_targets]

        timeline.append((t + dur * 0.15, onset_targets))
        timeline.append((t + dur * 0.50, peak_targets))
        timeline.append((t + dur * 0.85, decay_targets))
        t += dur
        
    timeline.append((t + 0.05, silence[:]))
    timeline.append((t + 0.30, [0.0] * NUM_BARS))
    return timeline, t + 0.35

class ScrewWidget(Widget):
    def __init__(self, size_dp=10, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(size_dp), dp(size_dp))
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r  = min(self.width, self.height) / 2 - dp(0.5)
        sl = r * 0.52
        with self.canvas:
            Color(*SCREW_BODY)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
            Color(0.16, 0.16, 0.18, 1)
            Ellipse(pos=(cx - r * 0.55, cy - r * 0.55),
                    size=(r * 1.10, r * 1.10))
            Color(*SCREW_SLOT)
            Line(points=[cx - sl, cy, cx + sl, cy], width=dp(1.3))
            Line(points=[cx, cy - sl, cx, cy + sl], width=dp(1.3))

class GrilleWidget(Widget):
    def __init__(self, rows=6, **kwargs):
        super().__init__(**kwargs)
        self._rows = rows
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return
        slot_h = dp(3.5)
        gap    = (self.height - self._rows * slot_h) / max(self._rows + 1, 1)
        px, pw = self.x + dp(6), self.width - dp(12)
        with self.canvas:
            for i in range(self._rows):
                y = self.y + gap + i * (slot_h + gap)
                Color(0.06, 0.06, 0.07, 1)
                Rectangle(pos=(px, y), size=(pw, slot_h))
                Color(0.17, 0.17, 0.19, 1)
                Rectangle(pos=(px, y + slot_h - dp(1)), size=(pw, dp(1)))

class AntennaWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(16), dp(20))
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*CHASSIS_EDGE)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[dp(3), dp(3), dp(2), dp(2)])
            Color(0.25, 0.25, 0.27, 1)
            RoundedRectangle(pos=(self.x + dp(3), self.y + dp(2)),
                             size=(self.width - dp(6), self.height - dp(4)),
                             radius=[dp(2)])

class PowerButton(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_on = False
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        cx, cy   = self.center_x, self.center_y
        r        = min(self.width, self.height) / 2
        ring_col = PWR_RING_ON  if self.is_on else PWR_RING_OFF
        icon_col = PWR_ICON_ON  if self.is_on else PWR_ICON_OFF
        bg_col   = PWR_BG_ON    if self.is_on else PWR_BG_OFF
        with self.canvas:
            Color(0.06, 0.06, 0.07, 1)
            Ellipse(pos=(cx - r - dp(3), cy - r - dp(3)),
                    size=((r + dp(3)) * 2, (r + dp(3)) * 2))
            Color(*ring_col)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))
            inner_r = r * 0.84
            Color(*bg_col)
            Ellipse(pos=(cx - inner_r, cy - inner_r),
                    size=(inner_r * 2, inner_r * 2))
            icon_r   = inner_r * 0.54
            lw       = dp(3.5)
            arc_start = 120 - 90
            arc_end   = 420 - 90
            Color(*icon_col)
            Line(ellipse=(cx - icon_r, cy - icon_r,
                          icon_r * 2, icon_r * 2,
                          arc_start, arc_end),
                 width=lw, cap="round")
            Line(points=[cx, cy - icon_r * 0.05,
                         cx, cy + icon_r * 1.06],
                 width=lw, cap="round")
            if not self.is_on:
                Color(0.30, 0.08, 0.08, 0.20)
                Ellipse(pos=(cx - inner_r, cy - inner_r),
                        size=(inner_r * 2, inner_r * 2))

    def set_state(self, on: bool):
        self.is_on = on
        self._draw()

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if hasattr(self, "_on_press_cb"):
                self._on_press_cb()
            return True
        return super().on_touch_up(touch)

class VisualizerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bar_heights    = [0.0] * NUM_BARS
        self.target_heights = [0.0] * NUM_BARS
        self.is_speaking    = False
        self._anim_event    = None
        self._peak_h        = [0.0] * NUM_BARS
        self._peak_decay    = [0.0] * NUM_BARS

        self._timeline      = []
        self._speak_gen     = 0
        
        self._bar_instr   = []
        self._peak_instr  = []
        self._peak_colors = []
        self._canvas_ready = False

        self.bind(pos=self._build_canvas, size=self._build_canvas)

    def _build_canvas(self, *args):
        if self.width <= 0 or self.height <= 0:
            return
        self.canvas.clear()
        self._bar_instr   = []
        self._peak_instr  = []
        self._peak_colors = []

        pad_x = dp(8)
        pad_y = dp(6)
        aw = self.width  - pad_x * 2
        ah = self.height - pad_y * 2
        ax = self.x + pad_x
        ay = self.y + pad_y
        gap_total = aw * 0.16
        gap       = gap_total / (NUM_BARS + 1)
        bar_w     = (aw - gap_total) / NUM_BARS

        self._vis = (ax, ay, aw, ah, gap, bar_w)

        with self.canvas:
            for i in range(NUM_BARS):
                Color(0.09, 0.13, 0.05, 0.90)
                br = Rectangle(pos=(0, 0), size=(bar_w, dp(4)))
                self._bar_instr.append(br)
                Color(0.04, 0.06, 0.02, 0.45)
                sr = Rectangle(pos=(0, 0), size=(bar_w * 0.20, dp(4)))
                self._bar_instr.append(sr)
                pc = Color(0.35, 0.62, 0.10, 0.0)
                pr = Rectangle(pos=(0, 0), size=(bar_w, dp(3)))
                self._peak_colors.append(pc)
                self._peak_instr.append(pr)

        self._canvas_ready = True
        self._paint_frame()

    def _paint_frame(self):
        if not self._canvas_ready:
            return
        ax, ay, aw, ah, gap, bar_w = self._vis
        peak_h = dp(3)

        for i in range(NUM_BARS):
            h  = max(dp(4), self.bar_heights[i] * ah)
            bx = ax + gap + i * (bar_w + gap)
            by = ay + (ah - h) / 2

            self._bar_instr[i * 2].pos  = (bx, by)
            self._bar_instr[i * 2].size = (bar_w, h)
            self._bar_instr[i * 2 + 1].pos  = (bx, by)
            self._bar_instr[i * 2 + 1].size = (bar_w * 0.20, h)

            ph = self._peak_h[i]
            if ph > 0.02:
                py_peak = ay + (ah - ph * ah) / 2 + ph * ah - peak_h
                self._peak_instr[i].pos  = (bx, py_peak)
                self._peak_instr[i].size = (bar_w, peak_h)
                self._peak_colors[i].a   = 0.90
            else:
                self._peak_colors[i].a = 0.0

    def load_phonemes(self, text):
        self._timeline, _ = build_phoneme_timeline(text)

    def start_speaking(self):
        self._speak_gen += 1
        self.is_speaking = True
        if self._anim_event is None:
            self._anim_event = Clock.schedule_interval(self._update, 1 / 60)
        self._fire_keyframe(0, self._speak_gen)

    def _fire_keyframe(self, idx, gen):
        if gen != self._speak_gen:
            return
        if idx >= len(self._timeline):
            return
        _, targets = self._timeline[idx]
        for i in range(NUM_BARS):
            self.target_heights[i] = targets[i]
        if idx < len(self._timeline) - 1:
            delay = max(0.001, self._timeline[idx + 1][0] - self._timeline[idx][0])
            Clock.schedule_once(
                lambda dt, i=idx + 1, g=gen: self._fire_keyframe(i, g),
                delay,
            )

    def stop_speaking(self):
        self._speak_gen += 1
        self.is_speaking = False
        for i in range(NUM_BARS):
            self.target_heights[i] = 0.0

    def _update(self, dt):
        for i in range(NUM_BARS):
            diff = self.target_heights[i] - self.bar_heights[i]
            if abs(diff) > 0.002:
                self.bar_heights[i] += diff * LERP_SPEED
            else:
                self.bar_heights[i] = self.target_heights[i]

            if self.bar_heights[i] > self._peak_h[i]:
                self._peak_h[i]     = self.bar_heights[i]
                self._peak_decay[i] = 0.0
            else:
                self._peak_decay[i] += dt
                if self._peak_decay[i] > 0.12:
                    self._peak_h[i] = max(
                        self.bar_heights[i],
                        self._peak_h[i] - dt * 0.80,
                    )

        all_idle = all(h < 0.005 for h in self.bar_heights)
        if all_idle and not self.is_speaking:
            if self._anim_event:
                self._anim_event.cancel()
                self._anim_event = None
            self._peak_h     = [0.0] * NUM_BARS
            self._peak_decay = [0.0] * NUM_BARS

        self._paint_frame()


class QueryButton(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.question = ""
        self.active   = False
        self.disabled = True

        with self.canvas.before:
            self._edge_c = Color(*QUERY_DIS_EDGE)
            self._edge_r = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(5)])
            self._bg_c   = Color(*QUERY_DIS_BG)
            self._bg_r   = RoundedRectangle(
                pos=(self.x + dp(1), self.y + dp(1)),
                size=(self.width - dp(2), self.height - dp(2)),
                radius=[dp(4)])
            self._dot_c  = Color(*QUERY_DIS_EDGE)
            self._dot_e  = Ellipse(
                pos=(self.x + dp(8), self.center_y - dp(2)),
                size=(dp(4), dp(4)))

        pad = Widget(size_hint_x=None, width=dp(18))

        self._label = Label(
            text="· · ·",
            font_size=DECENT_FONT,
            bold=True,
            halign="center",
            valign="middle",
            color=QUERY_DIS_TEXT,
            size_hint=(1, 1),
        )
        self._label.bind(size=self._label.setter("text_size"))

        self.add_widget(pad)
        self.add_widget(self._label)

        self.bind(pos=self._upd_bg, size=self._upd_bg)

    def _upd_bg(self, *args):
        self._edge_r.pos  = self.pos
        self._edge_r.size = self.size
        self._bg_r.pos    = (self.x + dp(1), self.y + dp(1))
        self._bg_r.size   = (self.width - dp(2), self.height - dp(2))
        self._dot_e.pos   = (self.x + dp(8), self.center_y - dp(2))

    def _apply_style(self):
        if self.disabled:
            e, b, d, tc = QUERY_DIS_EDGE, QUERY_DIS_BG, QUERY_DIS_EDGE, QUERY_DIS_TEXT
        elif self.active:
            e, b, d, tc = QUERY_ACTIVE_EDGE, QUERY_ACTIVE_BG, QUERY_ACTIVE_EDGE, QUERY_TEXT_ACT
        else:
            e, b, d, tc = QUERY_EDGE, QUERY_BG, QUERY_EDGE, QUERY_TEXT
        self._edge_c.rgba  = list(e)
        self._bg_c.rgba    = list(b)
        self._dot_c.rgba   = list(d)
        self._label.color  = tc

    def set_active(self, active: bool):
        self.active = active
        self._apply_style()

    def set_disabled(self, disabled: bool):
        self.disabled = disabled
        self._apply_style()

    def set_text(self, text: str, question: str):
        self._label.text = text
        self.question    = question
        self._apply_style()

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            if hasattr(self, "_on_press_cb"):
                self._on_press_cb(self)
            return True
        return super().on_touch_up(touch)

class SpiritBoxApp(App):
    def build(self):
        self.title          = "SPIRIT BOX"
        self.is_powered     = False
        self.is_busy        = False
        self._static_sound  = None
        self._scare_sound   = None
        self._jumpscare_active = False

        self._static_wav_path  = _generate_wav(30.0, 22050, 5000, "flat")
        self._scare_wav_path   = _generate_wav(5.0, 22050, 32000, "burst")

        root = self._build_ui()
        Clock.schedule_once(lambda dt: self._refresh_questions(), 0.3)
        Clock.schedule_once(lambda dt: self._preload_sounds(), 0.5)
        return root

    def _preload_sounds(self):
        self._static_sound = SoundLoader.load(self._static_wav_path)
        if self._static_sound:
            self._static_sound.loop   = True
            self._static_sound.volume = 0.09

        self._scare_sound = SoundLoader.load(self._scare_wav_path)
        if self._scare_sound:
            self._scare_sound.loop   = False
            self._scare_sound.volume = 1.0

    def _start_static(self):
        if self._static_sound and self._static_sound.state != "play":
            self._static_sound.play()

    def _stop_static(self):
        if self._static_sound and self._static_sound.state == "play":
            self._static_sound.stop()

    def _build_ui(self):
        root = BoxLayout(
            orientation="vertical",
            padding=[dp(14), dp(12), dp(14), dp(140)],
            spacing=dp(12),
        )
        with root.canvas.before:
            Color(*CHASSIS_TOP)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd_bg, size=self._upd_bg)

        root.add_widget(self._make_top_bar())
        root.add_widget(self._make_lcd())
        root.add_widget(self._make_power_zone())
        root.add_widget(self._make_query_section())
        root.add_widget(self._make_grille_footer())
        return root

    def _upd_bg(self, inst, val):
        self._bg.pos  = inst.pos
        self._bg.size = inst.size

    def _make_top_bar(self):
        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(38),
        )
        row.add_widget(AntennaWidget())

        center = BoxLayout(orientation="vertical")
        title = Label(
            text="[b]SPIRIT BOX[/b]", markup=True,
            font_size=DECENTER_FONT, color=(0.62, 0.68, 0.60, 1),
            halign="center", valign="middle",
        )
        title.bind(size=title.setter("text_size"))
        sub = Label(
            text="MODEL XC2816-67",
            font_size=NORMAL_FONT, color=(0.30, 0.34, 0.28, 1),
            halign="center", valign="middle",
        )
        sub.bind(size=sub.setter("text_size"))
        center.add_widget(title)
        center.add_widget(sub)
        row.add_widget(center)

        right = BoxLayout(size_hint_x=None, width=dp(22))
        right.add_widget(ScrewWidget(size_dp=9))
        row.add_widget(right)
        return row

    def _make_lcd(self):
        lcd_outer = BoxLayout(size_hint_y=None, height=dp(300))

        with lcd_outer.canvas.before:
            self._lcd_border_c = Color(*LCD_BORDER_OFF)
            self._lcd_border_r = RoundedRectangle(
                pos=lcd_outer.pos, size=lcd_outer.size, radius=[dp(6)])
            self._lcd_bg_c = Color(*LCD_GREEN_OFF)
            self._lcd_bg_r = RoundedRectangle(
                pos=(lcd_outer.x + dp(3), lcd_outer.y + dp(3)),
                size=(lcd_outer.width - dp(6), lcd_outer.height - dp(6)),
                radius=[dp(4)])

        lcd_outer.bind(pos=self._upd_lcd, size=self._upd_lcd)

        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(10), dp(8), dp(10), dp(8)],
            spacing=dp(4),
        )

        top_row = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(4))
        self._status_lbl = Label(
            text="STANDBY", font_size=COMMON_FONT, color=LCD_TEXT_OFF,
            bold=True, halign="left", valign="middle",
        )
        self._status_lbl.bind(size=self._status_lbl.setter("text_size"))
        self._mode_lbl = Label(
            text="FM SWEEP", font_size=COMMON_FONT, color=LCD_TEXT_OFF,
            halign="center", valign="middle",
        )
        self._mode_lbl.bind(size=self._mode_lbl.setter("text_size"))
        self._freq_lbl = Label(
            text="---.-- MHz", font_size=COMMON_FONT, color=LCD_TEXT_OFF,
            bold=True, halign="right", valign="middle",
        )
        self._freq_lbl.bind(size=self._freq_lbl.setter("text_size"))
        top_row.add_widget(self._status_lbl)
        top_row.add_widget(self._mode_lbl)
        top_row.add_widget(self._freq_lbl)

        self._visualizer = VisualizerWidget()

        self._response_lbl = Label(
            text="", font_size=BIG_FONT, bold=True, color=LCD_TEXT_OFF,
            halign="center", valign="middle",
            size_hint_y=None, height=dp(30),
        )
        self._response_lbl.bind(size=self._response_lbl.setter("text_size"))

        inner.add_widget(top_row)
        inner.add_widget(self._visualizer)
        inner.add_widget(self._response_lbl)
        lcd_outer.add_widget(inner)
        return lcd_outer

    def _upd_lcd(self, inst, val):
        self._lcd_border_r.pos  = inst.pos
        self._lcd_border_r.size = inst.size
        self._lcd_bg_r.pos  = (inst.x + dp(3), inst.y + dp(3))
        self._lcd_bg_r.size = (inst.width - dp(6), inst.height - dp(6))

    def _make_power_zone(self):
        zone = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(82),
            spacing=dp(8),
        )
        left = BoxLayout(orientation="vertical", size_hint_x=0.38)
        self._pwr_status_lbl = Label(
            text="POWER OFF", font_size=COMMON_FONT,
            color=(0.38, 0.15, 0.15, 1), bold=True,
            halign="left", valign="middle",
        )
        self._pwr_status_lbl.bind(size=self._pwr_status_lbl.setter("text_size"))
        serial = Label(
            text="2026-0415-420\nFM/AM 76-108",
            font_size=NORMAL_FONT, color=(0.25, 0.27, 0.24, 1),
            halign="left", valign="middle",
        )
        serial.bind(size=serial.setter("text_size"))
        left.add_widget(self._pwr_status_lbl)
        left.add_widget(serial)

        btn_wrap = BoxLayout(
            orientation="vertical", size_hint_x=0.26,
            padding=[dp(6), dp(6), dp(6), dp(6)],
        )
        self._power_btn = PowerButton()
        self._power_btn._on_press_cb = self._toggle_power
        btn_wrap.add_widget(self._power_btn)

        right = BoxLayout(orientation="vertical", size_hint_x=0.36)
        sweep = Label(
            text="SWEEP RATE\n100ms",
            font_size=NORMAL_FONT, color=(0.25, 0.27, 0.24, 1),
            halign="right", valign="middle",
        )
        sweep.bind(size=sweep.setter("text_size"))
        scr_row = BoxLayout(size_hint_y=None, height=dp(12))
        scr_row.add_widget(Widget())
        scr_row.add_widget(ScrewWidget(size_dp=8))
        right.add_widget(sweep)
        right.add_widget(scr_row)

        zone.add_widget(left)
        zone.add_widget(btn_wrap)
        zone.add_widget(right)
        return zone

    def _make_query_section(self):
        section_h = dp(16) + 3 * dp(52) + 3 * dp(7)
        outer = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=section_h,
            spacing=dp(7),
        )

        hdr_row = BoxLayout(size_hint_y=None, height=dp(16))
        hdr_row.add_widget(ScrewWidget(size_dp=7))
        hdr = Label(
            text="QUESTION SELECTION",
            font_size=NORMALISH_FONT, color=(0.30, 0.34, 0.28, 1),
            bold=True, halign="center", valign="middle",
        )
        hdr.bind(size=hdr.setter("text_size"))
        hdr_row.add_widget(hdr)
        hdr_row.add_widget(ScrewWidget(size_dp=7))
        outer.add_widget(hdr_row)

        self._query_btns = []
        for _ in range(3):
            btn = QueryButton(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(52),
            )
            btn._on_press_cb = self._on_query
            self._query_btns.append(btn)
            outer.add_widget(btn)

        return outer

    def _make_grille_footer(self):
        foot = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(46),
            spacing=dp(4),
        )
        foot.add_widget(GrilleWidget(rows=5, size_hint_y=None, height=dp(32)))
        note = Label(
            text="BULLSHIT INC  ·  MODEL XC2816-67  ·  IDIOTIC USE ONLY",
            font_size=SMALL_FONT, color=(0.20, 0.22, 0.18, 1),
            halign="center", valign="middle",
            size_hint_y=None, height=dp(12),
        )
        note.bind(size=note.setter("text_size"))
        foot.add_widget(note)
        return foot
        
    def _refresh_questions(self):
        pool = list(QUESTIONS.keys())
        random.shuffle(pool)
        for i, btn in enumerate(self._query_btns):
            btn.set_text(pool[i].upper(), pool[i])

    def _toggle_power(self, *args):
        if self.is_powered:
            return
        self.is_powered = not self.is_powered
        self._power_btn.set_state(self.is_powered)
        if self.is_powered:
            self._lcd_border_c.rgba = list(LCD_BORDER_ON)
            self._lcd_bg_c.rgba     = list(LCD_GREEN_ON)
            self._set_lcd_text(LCD_TEXT_ON)
            self._status_lbl.text      = "SCANNING"
            self._mode_lbl.text        = "FM SWEEP"
            self._freq_lbl.text        = f"{random.uniform(76.0, 108.0):.2f} MHz"
            self._pwr_status_lbl.text  = "POWER ON"
            self._pwr_status_lbl.color = (0.18, 0.72, 0.28, 1)
            for btn in self._query_btns:
                btn.set_disabled(False)
            self._start_static()
        else:
            self._lcd_border_c.rgba = list(LCD_BORDER_OFF)
            self._lcd_bg_c.rgba     = list(LCD_GREEN_OFF)
            self._set_lcd_text(LCD_TEXT_OFF)
            self._status_lbl.text      = "STANDBY"
            self._mode_lbl.text        = "FM SWEEP"
            self._freq_lbl.text        = "---.-- MHz"
            self._response_lbl.text    = ""
            self._pwr_status_lbl.text  = "POWER OFF"
            self._pwr_status_lbl.color = (0.38, 0.15, 0.15, 1)
            self._visualizer.stop_speaking()
            for btn in self._query_btns:
                btn.set_disabled(True)
                btn.set_active(False)
            self.is_busy = False
            self._stop_static()

    def _set_lcd_text(self, color):
        self._status_lbl.color   = color
        self._mode_lbl.color     = color
        self._freq_lbl.color     = color
        self._response_lbl.color = color

    def _on_query(self, btn):
        if not self.is_powered or self.is_busy or self._jumpscare_active:
            return

        if random.random() < 0.02:
            self._trigger_jumpscare()
            return

        question = btn.question
        category = QUESTIONS.get(question, "sign")
        response = random.choice(GHOST_RESPONSES[category])
        delay    = random.uniform(1.5, 3.0)

        self._visualizer.load_phonemes(response)

        self.is_busy = True
        for b in self._query_btns:
            b.set_disabled(True)
            b.set_active(False)
        btn.set_active(True)

        self._status_lbl.text   = "SCANNING..."
        self._response_lbl.text = "· · ·"
        self._freq_lbl.text     = f"{random.uniform(76.0, 108.0):.2f} MHz"

        threading.Thread(
            target=self._ghost_sequence,
            args=(response, delay, btn),
            daemon=True,
        ).start()

    def _trigger_jumpscare(self):
        self._jumpscare_active = True
        self.is_busy = True

        for b in self._query_btns:
            b.set_disabled(True)
            b.set_active(False)

        self._stop_static()

        if self._scare_sound:
            self._scare_sound.volume = 1.0
            self._scare_sound.play()

        response = random.choice(JUMPSCARE_RESPONSES)

        self._lcd_border_c.rgba = [0.90, 0.05, 0.05, 1]
        self._lcd_bg_c.rgba     = [0.60, 0.02, 0.02, 1]
        self._status_lbl.color  = (1, 0, 0, 1)
        self._mode_lbl.color    = (1, 0, 0, 1)
        self._freq_lbl.color    = (1, 0, 0, 1)
        self._response_lbl.color = (1, 1, 1, 1)
        self._status_lbl.text   = ">> INTRUSION"
        self._freq_lbl.text     = "!!!!!!! MHz"
        self._response_lbl.text = response

        self._visualizer.load_phonemes(response)
        self._visualizer.start_speaking()

        Clock.schedule_once(self._jumpscare_shutdown, 4.0)

    def _jumpscare_shutdown(self, dt):
        self._visualizer.stop_speaking()
        self._response_lbl.text = "IT IS HERE"
        self._status_lbl.text   = "SIGNAL LOST"
        self._freq_lbl.text     = "--- --- ---"

        Clock.schedule_once(self._do_shutdown, 1.5)

    def _do_shutdown(self, dt):
        self._jumpscare_active = False
        self.is_busy    = False
        self.is_powered = False
        self._power_btn.set_state(False)
        self._lcd_border_c.rgba    = list(LCD_BORDER_OFF)
        self._lcd_bg_c.rgba        = list(LCD_GREEN_OFF)
        self._set_lcd_text(LCD_TEXT_OFF)
        self._status_lbl.text      = "STANDBY"
        self._mode_lbl.text        = "FM SWEEP"
        self._freq_lbl.text        = "---.-- MHz"
        self._response_lbl.text    = ""
        self._pwr_status_lbl.text  = "POWER OFF"
        self._pwr_status_lbl.color = (0.38, 0.15, 0.15, 1)
        self._visualizer.stop_speaking()
        for b in self._query_btns:
            b.set_disabled(True)
            b.set_active(False)
        self._stop_static()

    def _ghost_sequence(self, response, delay, btn):
        time.sleep(delay)
        Clock.schedule_once(lambda dt: self._on_speak_start(response), 0)

        spoken = False
        try:
                speakf(response) #p = multiprocessing.Process(target=speakf, args=(response,)); p.start(); p.join()
        except Exception as e:
            print(f"TTS error: {e}")

        if not spoken:
            est = max(1.5, len(response.split()) * 0.70)
            time.sleep(est)

        Clock.schedule_once(lambda dt: self._on_speak_end(btn), 0)

    def _on_speak_start(self, response):
        self._response_lbl.text = response
        self._status_lbl.text   = ">> CONTACT"
        self._freq_lbl.text     = f"{random.uniform(76.0, 108.0):.2f} MHz"
        self._visualizer.start_speaking()

    def _on_speak_end(self, btn):
        self._visualizer.stop_speaking()
        self._status_lbl.text = "STANDBY"
        btn.set_active(False)
        self.is_busy = False
        self._refresh_questions()
        if self.is_powered:
            for b in self._query_btns:
                b.set_disabled(False)

if __name__ == "__main__":
    SpiritBoxApp().run()