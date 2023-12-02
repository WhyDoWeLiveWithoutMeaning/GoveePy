import logging
import socket
import json
import time

from .Objects import Color

_MULTICAST_GROUP = '239.255.255.250'
_MULTICAST_PORT = 4001
_RESPONSE_IP = '0.0.0.0'
_RESPONSE_PORT = 4002
_DEVICE_PORT = 4003

class GoveeDeviceLocal:

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

    def _listen_for_response(self) -> dict:
        logging.info("Listening for response")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind((_RESPONSE_IP, _RESPONSE_PORT))
        while True:
            try:
                recieved, resp_addr = sock.recvfrom(1024)
                recieved.decode("utf-8")
                try:
                    data = json.loads(recieved)
                    logging.info("Response from %s, %s",resp_addr, data)
                    return data
                except json.JSONDecodeError as e:
                    logging.error("Error decoding JSON: %s", e)
            except socket.error:
                pass

    def _send_request(self, command: dict, *, listen: bool = False) -> dict | None:
        data: dict | None = None

        r_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps({
            "msg": command
        }).encode("utf-8")

        try:
            r_sock.sendto(message, (self._ip, _DEVICE_PORT))
            logging.info("Request sent to %s:%s, %s", self._ip, _DEVICE_PORT, command)
        except Exception:
            logging.error("Request Failed")
        finally:
            r_sock.close()
            if listen:
                data = self._listen_for_response()
        return data

    def turn_on(self):
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
        self._send_request({
            "cmd" : "brightness",
            "data": {
                "value": brightness % 101
            }
        })
        self._brightness = brightness % 101

    def set_color(self, r: int, g: int, b: int, temp: int = 0):
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
        response = self._send_request({
            "cmd": "devStatus",
            "data": {}
        }, listen=True)["msg"]["data"]

        self._state = bool(response.get("onOff", 0))
        self._brightness = response.get("brightness", 0)
        self._color = Color(**response["color"]) if "color" in response else Color(0,0,0)
        self._color_tem = response.get("ColorTemInKelvin", 0)

    def update(self):
        self._update_device_state()

    @property
    def on(self):
        return self._state
    
    @property
    def off(self):
        return not self._state

    @property
    def ip(self):
        return self._ip
    
    @property
    def device(self):
        return self._device
    
    @property
    def model(self):
        return self._model

    def __str__(self):
        return f"<LocalGoveeDevice || {self.ip = }|{self.device = }|{self.model = }>"
    
    def __repr__(self):
        return f"<LocalGoveeDevice || {self.ip = }|{self.device = }|{self.model = }>"

class GoveeLocal:

    _devices = []

    def __init__(self, *, timeout: int = 1):
        self._timeout = timeout

    def get_devices(self):
        self._send_scan_request()

    def get_device_by_device(self, device: str) -> GoveeDeviceLocal | None:
        dev = list(filter(lambda x: x.device == device, self._devices))
        return dev[0] if len(dev) > 0 else None
    
    def get_device_by_ip(self, ip: str) -> GoveeDeviceLocal | None:
        dev = list(filter(lambda x: x.ip == ip, self._devices))
        return dev[0] if len(dev) > 0 else None

    def _send_scan_request(self):
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
            logging.info("Request sent to %s:%s", _MULTICAST_GROUP, _MULTICAST_PORT)
        except socket.error as e:
            logging.error("Error Sending Request to %s:%s | %s", _MULTICAST_GROUP, _MULTICAST_PORT, e)
        finally:
            send_socket.close()
        self._start_udp_server()
        return self._devices

    def _start_udp_server(self):
        # Create a UDP socket for receiving responses
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #Set it to Non-Blocking
        server_socket.setblocking(0)

        # Bind the socket to the server address and port
        server_socket.bind((_RESPONSE_IP, _RESPONSE_PORT))

        logging.info("UDP server listening on %s:%s", _RESPONSE_IP, _RESPONSE_PORT)

        start_time = time.time()

        while True:
            try:
                # Receive data and the address of the sender
                data, address = server_socket.recvfrom(1024)

                # Decode the received JSON message
                decoded_data = data.decode('utf-8')
                try:
                    json_data = json.loads(decoded_data)
                    logging.info("Recieved Data: %s", json_data)
                    self._handle_response(json_data, address)
                except json.JSONDecodeError as e:
                    logging.error("Error decoding JSON: %s", e)

            except socket.error:
                # Handle socket error (e.g., no data available)
                pass

            # Check if the timeout has been reached
            if time.time() - start_time > self._timeout:
                logging.info("Timeout reached. Stopping UDP server.")
                break
        logging.info("Socket Closed()")
        # Close the receiving socket when done
        server_socket.close()
        for device in self._devices:
            device.update()

    def _handle_response(self, response_data, sender_address):
        # Process the received response (customize as needed)
        self._devices.append(GoveeDeviceLocal(
            response_data["msg"]["data"]["ip"],
            response_data["msg"]["data"]["device"],
            response_data["msg"]["data"]["sku"]
        ))
        logging.info("Received response from %s: %s", sender_address, response_data)

    @property
    def devices(self):
        return self._devices