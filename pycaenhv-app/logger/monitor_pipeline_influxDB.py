import os
import threading
import time
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS

from .pipeline_factory import MonitorPipelineBase


class InfluxMonitorPipeline(MonitorPipelineBase):
    def __init__(self):
        self.buffer = {
            "hv_vmon": [],
            "hv_imon": [],
            "hv_status": [],
            "hv_v0": [],
            "hv_i0": [],
            "hv_control_status": [],
            "hv_channels": []
        }
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        self.url = os.environ.get("INFLUXDB_URL")
        self.token = os.environ.get("INFLUXDB_TOKEN")
        self.org = os.environ.get("INFLUXDB_ORG")
        self.bucket = os.environ.get("INFLUXDB_BUCKET")

        self.client = InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.channel_name_records = {}

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        self.client.close()

    def _flush_loop(self):
        while self._running:
            time.sleep(5)
            self.flush()

    def flush(self):
        with self._lock:
            for measurement, points in self.buffer.items():
                if points:
                    self.write_api.write(bucket=self.bucket, org=self.org, record=points)
                    self.buffer[measurement] = []

    def push_vmon(self, channel, vmon, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc)
        point = Point("hv_vmon").tag("channel", str(channel)).field("Vmon", float(vmon)).time(timestamp)
        with self._lock:
            self.buffer["hv_vmon"].append(point)

    def push_imon(self, channel, imon, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc)
        point = Point("hv_imon").tag("channel", str(channel)).field("Imon", float(imon)).time(timestamp)
        with self._lock:
            self.buffer["hv_imon"].append(point)

    def push_status(self, channel, status, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc)
        point = Point("hv_status").tag("channel", str(channel)).field("status", status).time(timestamp)
        with self._lock:
            self.buffer["hv_status"].append(point)

    def push_v0(self, channel, v0, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc)
        point = Point("hv_v0").tag("channel", str(channel)).field("V0", float(v0)).time(timestamp)
        with self._lock:
            self.buffer["hv_v0"].append(point)

    def push_i0(self, channel, i0, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc)
        point = Point("hv_i0").tag("channel", str(channel)).field("I0", float(i0)).time(timestamp)
        with self._lock:
            self.buffer["hv_i0"].append(point)

    def push_control_status(self, channel, control_status, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc)
        point = Point("hv_control_status").tag("channel", str(channel)).field("control_status", control_status).time(timestamp)
        with self._lock:
            self.buffer["hv_control_status"].append(point)

    def push_metadata(self, channel, name, valid_from=None):
        timestamp = valid_from or datetime.now(timezone.utc)
        ch = str(channel)

        # Close previous name interval if exists
        if ch in self.channel_name_records:
            prev_name, prev_time = self.channel_name_records[ch]
            prev_point = (
                Point("hv_channels")
                .tag("channel", ch)
                .field("name", prev_name)
                .field("valid_from", prev_time.isoformat())
                .field("valid_to", timestamp.isoformat())
                .time(prev_time)
            )
            with self._lock:
                self.buffer["hv_channels"].append(prev_point)

        # Register new name without valid_to yet
        new_point = (
            Point("hv_channels")
            .tag("channel", ch)
            .field("name", name)
            .field("valid_from", timestamp.isoformat())
            .time(timestamp)
        )
        with self._lock:
            self.buffer["hv_channels"].append(new_point)

        self.channel_name_records[ch] = (name, timestamp)
