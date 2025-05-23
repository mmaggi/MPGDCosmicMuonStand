from hv.interface import HVSystem, default_mode
from hv.fake_sy1527 import FakeSY1527
# from real_sy1527 import RealSY1527  # Uncomment when available
import os


def get_hv_system(mode: str = None) -> HVSystem:
    mode = mode or default_mode

    if mode == "fake":
        # Determine which file to use
        config_dir = "config"
        saved_file = os.path.join(config_dir, "hv_saved.json")
        default_file = os.path.join(config_dir, "hv_config.json")

        if os.path.exists(saved_file):
            print("Saved configuration found.")
            print("  [1] Load saved configuration (hv_saved.json)")
            print("  [2] Load default configuration (hv_config.json)")
            choice = input("Select configuration to load [1/2]: ").strip()
            config_path = saved_file if choice in ("", "1") else default_file
        else:
            print("No saved configuration found. Loading default.")
            config_path = default_file

        hv = FakeSY1527(config_path=config_path)

    elif mode == "real":
        raise NotImplementedError("RealSY1527 backend not yet implemented")
        # hv = RealSY1527(ip="192.168.1.100", user="admin", password="admin", config_path="hv_config.json")

    else:
        raise ValueError(f"Invalid HV system mode: {mode}")

    hv.init()
    return hv
