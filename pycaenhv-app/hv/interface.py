from abc import ABC, abstractmethod

default_mode = "real"

class HVSystem(ABC):
    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def turn_on(self, ch):
        pass

    @abstractmethod
    def turn_off(self, ch):
        pass

    @abstractmethod
    def set_voltage(self, ch, V0):
        pass

    @abstractmethod
    def get_status(self, ch):
        pass

    @abstractmethod
    def stop(self):
        pass

