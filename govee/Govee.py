import requests
from abc import abstractmethod
from enum import Enum
from typing import List

BASE_URL = "https://developer-api.govee.com"

class Command(Enum):
    TURN = 'turn'
    BRIGHTNESS = 'brightness'
    COLOR = 'color'
    COLORTEM = 'colortem'

class GoveeDevice:

    _model: str
    _device: str
    _name: str

    _key: str

    _on: bool = None

    def __init__(self, model: str = "", device: str = "", name: str = "", key: str = ""):
        self._model = model
        self._device = device
        self._name = name
        self._key = key

    def _make_request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        if not kwargs.get("headers", None):
            kwargs["headers"] = {
                "Govee-API-Key": self._key
            }
        response = requests.request(method, url, *args, **kwargs)
        return response.json()

    @abstractmethod
    def _command(self, command):
        pass

    @property
    def name(self):
        return self._name

    @property
    def on(self):
        return self._on
    
    @property
    def off(self):
        return not self._on

    @abstractmethod
    def _update(self):
        pass

    def turn_on(self):
        self._command(
            {
                "name": "turn",
                "value": "on"
            }
        )

    def turn_off(self):
        self._command(
            {
                "name": "turn",
                "value": "off"
            }
        )



class GoveeLight(GoveeDevice):

    def _command(self, command):
        self._make_request(
            "PUT",
            f"{BASE_URL}/v1/devices/control",
            json = {
                "device": self._device,
                "model": self._model,
                "cmd": command
            }
        )

    def update(self):
        response = self._make_request(
            "GET",
            f"{BASE_URL}/v1/devices/state",
            params={
                "device": self._device,
                "model": self._model
            }
        )
        self._on = update

class GoveeAppliance(GoveeDevice):

    def _command(self, command):
        self._make_request(
            "PUT",
            f"{BASE_URL}/v1/appliance/devices/control",
            json = {
                "device": self._device,
                "model": self._model,
                "cmd": command
            }
        )


class Govee:

    _key: str
    _devices: List[GoveeDevice] = None
    _device_rate_limits: List

    def __init__(self, key: str):
        self._key = key

    def _make_request(self, method: str, url: str, *args, **kwargs):
        if not kwargs.get("headers", None):
            kwargs["headers"] = {
                "Govee-API-Key": self._key
            }
        response = requests.request(method, url, *args, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            raise 

    def get_devices(self, *, update: bool = False):
        if not self._devices or update:
            response = self._make_request(
                "GET",
                f"{BASE_URL}/v1/devices"
            )

        else:
            return self._devices
        
    def get_device_by_name(self, name: str) -> GoveeDevice:
        for device in self._devices:
            if device.name is name:
                return device
        return None
    
    def get_device_by_model(self, model: str) -> GoveeDevice:
        for device in self._devices:
            if device._model is model:
                return device
        return None
    
    def get_device_by_address(self, address: str) -> GoveeDevice:
        for device in self._devices:
            if device._device is address:
                return device
        return None