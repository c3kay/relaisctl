from logging import getLogger
import RPi.GPIO as GPIO

logger = getLogger(__name__)

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
logger.debug(GPIO.VERSION)
logger.debug(GPIO.RPI_INFO)


class ZeroRelay:
    """
    Control the "Zero Relay" from SB Components via GPIO pins.

    https://github.com/sbcshop/Zero-Relay/blob/master/pizero_2relay.py
    """

    def __init__(self, relay_nr: int):
        pins = [15, 29]

        try:
            self.pin = pins[relay_nr-1]
        except IndexError:
            logger.error("Invalid relay_nr: %d", relay_nr)
            raise

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        """Toggle the Relais on ("Active")."""
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        """Toggle the Relais off ("At rest")."""
        GPIO.output(self.pin, GPIO.LOW)
