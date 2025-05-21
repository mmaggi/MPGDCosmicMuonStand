import json
import threading
import time
import random
from hv.interface import HVSystem


class FakeSY1527(HVSystem):
    def __init__(self, config_path="hv_config.json"):
        self.config_path = config_path
        self.state = {}
        self.running = False
        self._lock = threading.Lock()

    def init(self):
        with open(self.config_path) as f:
            config = json.load(f)
        self.state = {}
        for ch, settings in config["channels"].items():
            self.state[ch] = {
                "name": settings["name"],
                "V0": settings["V0"],
                "I0": settings["I0"],
                "ramp_up": settings["ramp_up"],
                "ramp_down": settings["ramp_down"],
                "status": settings.get("status", "OFF"),
                "Vmon": 0.0,
                "Imon": 0.0
            }
        self.running = True
        self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
        self._thread.start()

    def _simulate_loop(self):
        while self.running:
            with self._lock:
                for ch, s in self.state.items():
                    if s["status"] == "ON":
                        s["Vmon"] = random.gauss(s["V0"], 10.0)
                        s["Imon"] = random.gauss(s["I0"], 0.0001)
                    elif s["status"] == "OFF":
                        s["Vmon"] = 0.0
                        s["Imon"] = 0.0
                    elif s["status"] == "RAMPING_UP":
                        step = s["ramp_up"]
                        s["Vmon"] += step
                        if s["Vmon"] >= s["V0"]:
                            s["Vmon"] = s["V0"]
                            s["status"] = "ON"
                        s["Imon"] = s["I0"] / 2
                    elif s["status"] == "RAMPING_DOWN":
                        step = s["ramp_down"]
                        s["Vmon"] -= step
                        if s["Vmon"] <= 0:
                            s["Vmon"] = 0.0
                            s["status"] = "OFF"
                        s["Imon"] = s["I0"] / 2
            time.sleep(random.uniform(0.5, 1.5))

    def turn_on(self, ch):
        with self._lock:
            if ch in self.state and self.state[ch]["status"] == "OFF":
                self.state[ch]["status"] = "RAMPING_UP"

    def turn_off(self, ch):
        with self._lock:
            if ch in self.state and self.state[ch]["status"] == "ON":
                self.state[ch]["status"] = "RAMPING_DOWN"

    def set_voltage(self, ch, V0):
        with self._lock:
            if ch in self.state:
                self.state[ch]["V0"] = V0

    def get_status(self, ch):
        with self._lock:
            return dict(self.state[ch]) if ch in self.state else {}

    def stop(self):
        self.running = False
        if hasattr(self, "_thread") and self._thread.is_alive():
            self._thread.join()
