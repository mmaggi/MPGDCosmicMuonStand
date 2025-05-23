import json
import threading
import time
import random
from hv.interface import HVSystem
from logger.pipeline_factory import get_monitor_pipeline
from datetime import datetime, timezone

class FakeSY1527(HVSystem):
    def __init__(self, config_path="hv_config.json"):
        self.config_path = config_path
        self.state = {}
        self.running = False
        self._lock = threading.Lock()
        self.pipeline = get_monitor_pipeline()
        
    def init(self):
        with open(self.config_path) as f:
            config = json.load(f)

        for ch, cfg in config["channels"].items():
            self.pipeline.push_metadata(
                channel=ch,
                name=cfg["name"],
                valid_from=datetime.now(timezone.utc)
            )
            
        self.state = {}

        for chs, settings in config["channels"].items():
            ch = int(chs)
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
                        s["Imon"] = random.gauss(s["I0"]/100., 0.0001)
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
                    now = datetime.now(timezone.utc)
                    self.pipeline.push_vmon(ch, s["Vmon"], timestamp=now)
                    self.pipeline.push_imon(ch, s["Imon"], timestamp=now)
                    self.pipeline.push_status(ch, s["status"], timestamp=now)
            time.sleep(random.uniform(0.5, 1.5))

    def turn_on(self, chs):
        with self._lock:
            ch = int(chs)
            if ch in self.state and self.state[ch]["status"] == "OFF":
                self.state[ch]["status"] = "RAMPING_UP"
                self.pipeline.push_control_status(ch,"ON")
                
    def turn_off(self, chs):
        with self._lock:
            ch = int(chs)
            if ch in self.state and self.state[ch]["status"] == "ON":
                self.state[ch]["status"] = "RAMPING_DOWN"
                self.pipeline.push_control_status(ch,"OFF")

    def set_voltage(self, chs, V0):
        with self._lock:
            ch = int(chs)
            if ch in self.state:
                self.state[ch]["V0"] = V0
                self.pipeline.push_v0(ch, V0)

    def set_maxcurrent(self, chs, I0):
        with self._lock:
            ch = int(chs)
            if ch in self.state:
                self.state[ch]["I0"] = I0
                self.pipeline.push_i0(ch, I0)
                
    def set_name(self, ch, new_name):
        print(f" sono fake per set_name")
        with self._lock:
            print(f" In lock", ch)
            print(self.state)
            if ch in self.state:
                print(f"Setting name for channel {ch} to {new_name}")
                self.state[ch]["name"] = new_name
                self.pipeline.push_metadata(ch, new_name, valid_from=datetime.now(timezone.utc))

                
    def get_status(self, ch):
        with self._lock:
            return dict(self.state[ch]) if ch in self.state else {}

    def stop(self):
        self.running = False
        if hasattr(self, "_thread") and self._thread.is_alive():
            self._thread.join()
