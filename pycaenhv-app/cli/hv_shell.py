import cmd
import argparse
from hv.backend_factory import get_hv_system
import readline
import atexit
import os
import time
import json
import threading

HISTORY_FILE = os.path.expanduser("~/.hvhistory")

class HVCosmicStandShell(cmd.Cmd):
    intro = "Welcome to HVCosmicStand shell. Type help or ? to list commands."
    prompt = "HVCosmicStand> "

    def __init__(self, mode="fake"):
        super().__init__()
        self.mode = mode
        self.hv = get_hv_system(mode=mode)
        self.config_path = getattr(self.hv, "config_path", "hv_config.json")
        self.channel_list = list(self.hv.state.keys())
        self._init_history()
        self._start_autosave()

    def _init_history(self):
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
        atexit.register(readline.write_history_file, HISTORY_FILE)

    def _save_state_to_config(self):
        config = {"crate": "FakeSY1527", "channels": {}}
        for ch, state in self.hv.state.items():
            config["channels"][ch] = {
                "name": state["name"],
                "V0": state["V0"],
                "I0": state["I0"],
                "ramp_up": state["ramp_up"],
                "ramp_down": state["ramp_down"],
                "status": state["status"]
            }
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {self.config_path}.")

    def _start_autosave(self):
        if self.mode == "fake":
            def autosave_loop():
                while True:
                    time.sleep(60)
                    self._save_state_to_config()
            t = threading.Thread(target=autosave_loop, daemon=True)
            t.start()

    def do_edit(self, args):
        "Edit a channel parameter: edit <ch> <param> <value>"
        try:
            ch, param, val = args.split()
            if ch not in self.hv.state:
                print("Unknown channel.")
                return
            if param not in ["name", "V0", "I0", "ramp_up", "ramp_down"]:
                print("Invalid parameter. Use one of: name, V0, I0, ramp_up, ramp_down")
                return
            if param == "name":
                self.hv.state[ch][param] = val
            else:
                self.hv.state[ch][param] = float(val)
            print(f"Updated {param} for channel {ch} to {val}")
        except ValueError:
            print("Usage: edit <ch> <param> <value>")

    def complete_edit(self, text, line, begidx, endidx):
        tokens = line.split()
        if len(tokens) == 2:
            return [c for c in self.channel_list if c.startswith(text)]
        elif len(tokens) == 3:
            return [p for p in ["name", "V0", "I0", "ramp_up", "ramp_down"] if p.startswith(text)]
        else:
            return []

    def do_on(self, ch):
        "Turn ON a channel: on <ch>"
        self.hv.turn_on(ch)

    def complete_on(self, text, line, begidx, endidx):
        return [c for c in self.channel_list if c.startswith(text)]

    def do_off(self, ch):
        "Turn OFF a channel: off <ch>"
        self.hv.turn_off(ch)

    def complete_off(self, text, line, begidx, endidx):
        return [c for c in self.channel_list if c.startswith(text)]

    def do_set(self, args):
        "Set V0 for a channel: set <ch> <V0>"
        try:
            ch, v0 = args.split()
            self.hv.set_voltage(ch, float(v0))
        except ValueError:
            print("Usage: set <ch> <V0>")

    def do_maxI0(self, args):
        "Set I0 for a channel: maxI0 <ch> <I0>"
        try:
            ch, i0 = args.split()
            self.hv.set_maxcurrent(ch, float(i0))
        except ValueError:
            print("Usage: maxI0 <ch> <I0>")

    def complete_set(self, text, line, begidx, endidx):
        return [c for c in self.channel_list if c.startswith(text)]

    def do_get(self, ch):
        "Get status of a channel: get <ch>"
        status = self.hv.get_status(ch)
        print(status)

    def complete_get(self, text, line, begidx, endidx):
        return [c for c in self.channel_list if c.startswith(text)]

    def do_list(self, arg):
        "List all channels: list [short|long]"
        mode = arg.strip().lower() or "short"
        for ch in self.channel_list:
            status = self.hv.get_status(ch)
            if mode == "long":
                print(f"[{ch}] {status}")
            else:
                print(f"[{ch}] {status['name']} status={status['status']} Vmon={status['Vmon']:.1f}V Imon={status['Imon']*1*3:.2f}mA V0={status['V0']}V")

    def do_watch(self, arg):
        "Repeatedly list channel status every second: watch [short|long]"
        mode = arg.strip().lower() or "short"
        print("Press Ctrl+C to stop watching.")
        try:
            while True:
                print("\n--- Channel Status ---")
                for ch in self.channel_list:
                    status = self.hv.get_status(ch)
                    if mode == "long":
                        print(f"[{ch}] {status}")
                    else:
                        print(f"[{ch}] {status['name']} status={status['status']} Vmon={status['Vmon']:.1f}V Imon={status['Imon']*1e3:.2f}mA")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped watching.")
            self.lastcmd = ""
            
    def do_setname(self, arg):
        "Set a new name for a channel: setname <channel_id> <new_name>"
        try:
            ch, name = arg.split()
            ch = int(ch)
            self.hv.set_name(ch, name)
            print(f"Channel {ch} renamed to '{name}'")
        except ValueError:
            print("Usage: setname <channel_id> <new_name>")
        
    def do_save(self, _):
        "Save current HV configuration back to config file"
        if self.mode == "fake":
            self._save_state_to_config()
        elif self.mode == "real":
            print("In real mode, save will apply configuration to hardware (not yet implemented).")

    def do_exit(self, _):
        "Exit the shell"
        print("Exiting...")
        if self.mode == "fake":
            self._save_state_to_config()
        self.hv.stop()
        return True

    def do_EOF(self, _):
        return self.do_exit(_)


def main():
    parser = argparse.ArgumentParser(description="HV Cosmic Stand Shell")
    parser.add_argument("--mode", choices=["fake", "real"], default=None, help="HV backend mode")
    args = parser.parse_args()

    shell = HVCosmicStandShell(mode=args.mode or "fake")
    shell.cmdloop()


if __name__ == "__main__":
    main()

