import logging
import socket
import json
import time

from typing import List, Callable
from .Objects import Color

_LOG = logging.getLogger(__name__)

_MULTICAST_GROUP = '239.255.255.250'
_MULTICAST_PORT = 4001
_RESPONSE_IP = '0.0.0.0'
_RESPONSE_PORT = 4002
_DEVICE_PORT = 4003

class _Listener:

    def _listen_for_response(self, address, port, *,
                            timeout: int = None,
                            callback: Callable[[dict, str], None] = None
                            ) -> dict | None:
        _LOG.info("Listening for response")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind((address, port))
        if timeout:
            start = time.time()
        while True:
            try:
                recieved, resp_addr = sock.recvfrom(1024)
                recieved.decode("utf-8")
                try:
                    data = json.loads(recieved)
                    _LOG.info("Response from %s, %s",resp_addr, data)
                    if timeout:
                        callback(data, resp_addr)
                    else:
                        return data
                except json.JSONDecodeError as e:
                    _LOG.error("Error decoding JSON: %s", e)
            except socket.error:
                pass

            if timeout:
                if time.time() - start > timeout:
                    _LOG.info("Timeout reached. Stopping UDP server.")
                    break

class GoveeDeviceLocal(_Listener):
    """
    Class representing a Govee device

    :param str ip: the IP address of the device.
    :param str device: the unique device id.
    :param str model: the model of the device.
    """
    _ip: str
    _device: str
    _model: str

    _state: bool
    _brightness: int
    _color: Color
    _color_tem: int

    def __init__(self, ip: str, device: str, model: str) -> None:
        self._ip = ip
        self._device = device
        self._model = model

    def _send_request(self, command: dict, *, listen: bool = False) -> dict | None:
        """
        Sends a request to the device.

        :param command: The command to send.
        :param listen: Whether or not to listen for a response.
        """
        data: dict | None = None

        r_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps({
            "msg": command
        }).encode("utf-8")

        try:
            r_sock.sendto(message, (self._ip, _DEVICE_PORT))
            _LOG.info("Request sent to %s:%s, %s", self._ip, _DEVICE_PORT, command)
        except socket.error:
            _LOG.error("Request Failed")
        finally:
            r_sock.close()
            if listen:
                data = self._listen_for_response(_RESPONSE_IP, _RESPONSE_PORT)
        return data

    def turn_on(self):
        """
        Turns the device on. 

        :return: None
        """

        self._send_request(
            {
                "cmd" : "turn",
                "data": {
                    "value" : 1
                }
            }
        )
        self._state = True

    def turn_off(self):
        """
        Turns the device off.    

        :return: None
        """

        self._send_request(
            {
                "cmd" : "turn",
                "data": {
                    "value" : 0
                }
            }
        )
        self._state = False

    def set_brightness(self, brightness: int):
        """
        Set the brightness of the device.

        :param brightness: The brightness to set (1-100)
        :return: None
        """

        self._send_request({
            "cmd" : "brightness",
            "data": {
                "value": brightness % 101
            }
        })
        self._brightness = brightness % 101

    def set_color(self, r: int, g: int, b: int, temp: int = 0):
        """
        Set the color of the device.
        
        :param r: The red value (0-255)
        :param g: The green value (0-255)
        :param b: The blue value (0-255)
        :param temp: The color temperature (0-100)
        :return: None
        """

        self._send_request({
            "cmd": "colorwc",
            "data": {
                "color" : {
                    "r": r % 256,
                    "g": g % 256,
                    "b": b % 256
                },
                "colorTemInKelvin": temp
            }
        })
        self._color = Color(r%256, g%256, b%256)
        self._color_tem = temp

    def _update_device_state(self):
        """
        Updates the device state.
        """
        response = self._send_request({
            "cmd": "devStatus",
            "data": {}
        }, listen=True)["msg"]["data"]

        self._state = bool(response.get("onOff", 0))
        self._brightness = response.get("brightness", 0)
        self._color = Color(**response["color"]) if "color" in response else Color(0,0,0)
        self._color_tem = response.get("ColorTemInKelvin", 0)

    def update(self):
        """
        Updates the device state.
        """
        self._update_device_state()

    @property
    def on(self):
        """
        Returns whether or not the device is on.
        
        :return: bool
        """
        return self._state

    @property
    def off(self):
        """
        Returns whether or not the device is off.
        
        :return: bool
        """
        return not self._state

    @property
    def ip(self):
        """
        Returns the IP address of the device.
        
        :return: str
        """
        return self._ip

    @property
    def device(self):
        """
        Returns the unique device id.
        
        :return: str
        """
        return self._device

    @property
    def model(self):
        """
        Returns the model of the device.
        
        :return: str
        """
        return self._model

    def __str__(self):
        return f"<LocalGoveeDevice || {self.ip = }|{self.device = }|{self.model = }>"

    def __repr__(self):
        return f"<LocalGoveeDevice || {self.ip = }|{self.device = }|{self.model = }>"

class GoveeLocal(_Listener):
    """
    Class representing a Govee device
    
    :param int timeout: The timeout for the scan request.
    
    :var devices: A list of devices found on the network.
    
    :return: None
    """

    def __init__(self, *, timeout: int = 1):
        self._timeout = timeout
        self.__devices = []

    def get_devices(self):
        """
        Sends a scan request to the network and returns a list of devices found.
        
        :return: List[GoveeDeviceLocal]
        """
        return self._send_scan_request()

    def get_device_by_device(self, device: str) -> GoveeDeviceLocal | None:
        """
        Returns a device by its unique device id.

        :param device: The unique device id.
        
        :return: GoveeDeviceLocal | None
        """

        dev = list(filter(lambda x: x.device == device, self.__devices))
        return dev[0] if len(dev) > 0 else None
    
    def get_device_by_ip(self, ip: str) -> GoveeDeviceLocal | None:
        """
        Returns a device by its IP address.

        :param ip: The IP address of the device.

        :return: GoveeDeviceLocal | None
        """
        dev = list(filter(lambda x: x.ip == ip, self.__devices))
        return dev[0] if len(dev) > 0 else None
    
    def __handle_response(self, response_data, sender_address):
        """
        Handles a response from a device.
        """
        self.__devices.append(GoveeDeviceLocal(
            response_data["msg"]["data"]["ip"],
            response_data["msg"]["data"]["device"],
            response_data["msg"]["data"]["sku"]
        ))
        _LOG.info("Received response from %s: %s", sender_address, response_data)

    def _send_scan_request(self):
        """
        Sends a scan request to the network.
        """
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        send_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        request_message = json.dumps({
            "msg": {
                "cmd": "scan",
                "data": {
                    "account_topic": "reserve"
                }
            }
        }).encode('utf-8')
        try:
            send_socket.sendto(request_message, (_MULTICAST_GROUP, _MULTICAST_PORT))
            _LOG.info("Request sent to %s:%s", _MULTICAST_GROUP, _MULTICAST_PORT)
        except socket.error as e:
            _LOG.error("Error Sending Request to %s:%s | %s", _MULTICAST_GROUP, _MULTICAST_PORT, e)
        finally:
            send_socket.close()
        self._listen_for_response(_RESPONSE_IP, _RESPONSE_PORT, timeout=1, callback=self.__handle_response)
        for device in self.__devices:
            device.update()
        return self.__devices

    @property
    def devices(self):
        """
        Returns a list of cached devices found on the network.
        
        :return: List[GoveeDeviceLocal]
        """
        return self.__devices