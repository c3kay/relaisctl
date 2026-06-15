import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class Relais:
    """
    Control the Relais via GPIO pins.

    https://github.com/sbcshop/Zero-Relay/blob/master/pizero_2relay.py
    """

    def __init__(self, relais_pin: int):
        self.pin = relais_pin
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        """Toggle the Relais on ("Active")."""
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        """Toggle the Relais off ("At rest")."""
        GPIO.output(self.pin, GPIO.LOW)
