import logging
from typing import Any, Callable
from sys import stdout

import paho.mqtt.client as mqtt
from json import loads, JSONDecodeError

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(stdout)]
)

TOPIC = "homeassistant/binary_sensor/+/+/state"
DETECTED_STATUS = "Detected"


class XsenseMqtt:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        stations: list[str] | None = None,
    ) -> None:
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            clean_session = True
        )
        self._client.username_pw_set(username, password)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self._host = host
        self._port = port

        stations = stations or []
        self.alarms = {s: False for s in stations}
        self.sensors: dict[str, str] = {}

        self.on_detect: Callable[[str], None] | None = None
        self.on_clear: Callable[[str], None] | None = None

        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties,
    ) -> None:
        """Connection callback."""
        self.log.info(f"Connected to {self._host} with result code: {reason_code}")
        self.log.debug(f"Flags: {flags}")
        client.subscribe(TOPIC)

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Message callback."""
        try:
            json_msg = loads(msg.payload)
            status = json_msg["status"]
        except JSONDecodeError as e:
            self.log.error(f"Error decoding JSON from message: {e}")
            return

        for station, alarm in self.alarms.items():
            topic_path = msg.topic.split("/")

            # filter messages for smoke alarm status only
            if len(topic_path) >= 4 and topic_path[2].startswith(station) and topic_path[3].endswith("_smokealarm"):
                # sensor id consists of station prefix and sensor hex number
                sensor = topic_path[2]
                self.log.debug(
                    "Alarm status from '%s' at %f: %s",
                    sensor,
                    msg.timestamp,
                    status,
                )

                # record current sensor status
                self.sensors[sensor] = status

                # check status for each sensor of current station
                station_alarm = any([
                    status == DETECTED_STATUS
                    for sensor, status in self.sensors.items()
                    if sensor.startswith(station)
                ])

                # first occurrence of alarm if not already in alarm state
                if not alarm and station_alarm:
                    self.alarms[station] = True
                    self.log.info("Alarm detected from '%s'!", station)

                    if self.on_detect:
                        self.log.debug("Running detection callback")
                        self.on_detect(station)

                # currently in alarm state but no alarm detected
                if alarm and not station_alarm:
                    self.alarms[station] = False
                    self.log.info("Alarm cleared from '%s'!", station)

                    if self.on_clear:
                        self.log.debug("Running clear callback")
                        self.on_clear(station)


    def listen(self) -> None:
        """Connect to the MQTT broker and listen for incoming messages."""
        self._client.connect(self._host, self._port)
        try:
            self._client.loop_forever()
        finally:
            self._client.disconnect()


x = XsenseMqtt("kg-rpi.fritz.box", username="xsense", password="xsense", stations=["SBS5015A9D25D"])
x.listen()
