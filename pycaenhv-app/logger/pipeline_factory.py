import os
from abc import ABC, abstractmethod

# Only import once we know what to load
_default_pipeline = None

class MonitorPipelineBase(ABC):
    @abstractmethod
    def push_vmon(self, channel, vmon, timestamp=None):
        pass
        @abstractmethod
    def push_imon(self, channel, imon, timestamp=None):
        pass
        @abstractmethod
    def push_status(self, channel, status, timestamp=None):
        pass

    @abstractmethod
    def push_control_status(self, channel, control_status, timestamp=None):
        pass

    @abstractmethod
    def push_v0(self, channel, v0, timestamp=None):
        pass

    @abstractmethod
    def push_i0(self, channel, i0, timestamp=None):
        pass

    @abstractmethod
    def push_metadata(self, channel, name, valid_from=None):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass


def get_monitor_pipeline() -> MonitorPipelineBase:
    global _default_pipeline
    if _default_pipeline is not None:
        return _default_pipeline

    impl = os.environ.get("MONITOR_PIPELINE_IMPL", "influxdb").lower()

    if impl == "influxdb":
        from logger.monitor_pipeline_influxDB import InfluxMonitorPipeline
        _default_pipeline = InfluxMonitorPipeline()
    else:
        raise ValueError(f"Unknown monitor pipeline implementation: {impl}")

    _default_pipeline.start()
    return _default_pipeline


def stop_monitor_pipeline():
    global _default_pipeline
    if _default_pipeline:
        _default_pipeline.stop()
        _default_pipeline = None
