"""An example of how to setup and start an Accessory.
This is:
1. Create the Accessory object you want.
2. Add it to an AccessoryDriver, which will advertise it on the local network,
    setup a server to answer client queries, etc.
"""
import os, pigpio, logging, signal

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")


class FiftyFiftyHomeKit(Accessory):
    category = CATEGORY_LIGHTBULB
    def __init__(self, rgb_pins, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgb_pins = rgb_pins

        # Set our neopixel API services up using Lightbulb base
        serv_light = self.add_preload_service(
            'Lightbulb', chars=['On', 'Hue', 'Saturation', 'Brightness'])

        # Set our instance variables
        self.accessory_state = 0  # State of the neo light On/Off
        self.hue = 0  # Hue Value 0 - 360 Homekit API
        self.saturation = 100  # Saturation Values 0 - 100 Homekit API
        self.brightness = 100  # Brightness value 0 - 100 Homekit API

        # Configure our callbacks
        self.char_hue = serv_light.configure_char(
            'Hue', setter_callback=self.set_hue)
        self.char_saturation = serv_light.configure_char(
            'Saturation', setter_callback=self.set_saturation)
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_state)
        self.char_on = serv_light.configure_char(
            'Brightness', setter_callback=self.set_brightness)

        # Get pigpiod running on the RPi if it hasn't been done already
        os.system("sudo pigpiod")
        self.pi = pigpio.pi()

        for i in range(0, 3):
            self.pi.set_PWM_dutycycle(self.rgb_pins[i], server_rgb[i] / 255 * temp_strip_led_brightness)

    def set_state(self, value):
        self.accessory_state = value
        if value == 1:  # On
            self.set_hue(self.hue)
        else:
            self.update_neopixel_with_color(0, 0, 0)  # Off

    def set_hue(self, value):
        # Lets only write the new RGB values if the power is on
        # otherwise update the hue value only
        if self.accessory_state == 1:
            self.hue = value
            rgb_tuple = self.hsv_to_rgb(
                self.hue, self.saturation, self.brightness)
            if len(rgb_tuple) == 3:
                self.update_neopixel_with_color(
                    rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        else:
            self.hue = value

    def set_brightness(self, value):
        self.brightness = value
        self.set_hue(self.hue)

    def set_saturation(self, value):
        self.saturation = value
        self.set_hue(self.hue)

    def update_lights_with_color(self, red, green, blue):
        self.pi.set_PWM_dutycycle(self.rgb_pins[0], red)
        self.pi.set_PWM_dutycycle(self.rgb_pins[1], green)
        self.pi.set_PWM_dutycycle(self.rgb_pins[2], blue)

    def hsv_to_rgb(self, h, s, v):
        """
        This function takes
         h - 0 - 360 Deg
         s - 0 - 100 %
         v - 0 - 100 %
        """

        hPri = h / 60
        s = s / 100
        v = v / 100

        if s <= 0.0:
            return int(0), int(0), int(0)

        C = v * s  # Chroma
        X = C * (1 - abs(hPri % 2 - 1))

        RGB_Pri = [0.0, 0.0, 0.0]

        if 0 <= hPri <= 1:
            RGB_Pri = [C, X, 0]
        elif 1 <= hPri <= 2:
            RGB_Pri = [X, C, 0]
        elif 2 <= hPri <= 3:
            RGB_Pri = [0, C, X]
        elif 3 <= hPri <= 4:
            RGB_Pri = [0, X, C]
        elif 4 <= hPri <= 5:
            RGB_Pri = [X, 0, C]
        elif 5 <= hPri <= 6:
            RGB_Pri = [C, 0, X]
        else:
            RGB_Pri = [0, 0, 0]

        m = v - C

        return int((RGB_Pri[0] + m) * 255), int((RGB_Pri[1] + m) * 255), int((RGB_Pri[2] + m) * 255)


"""
An Accessory for Adafruit NeoPixels attached to GPIO Pin18
 Tested using Python 3.5/3.6 Raspberry Pi
 This device uses all available services for the Homekit Lightbulb API
 Note: RPi GPIO must be PWM. Neopixels.py will warn if wrong GPIO is used
       at runtime
 Note: This Class requires the installation of rpi_ws281x lib
       Follow the instllation instructions;
           git clone https://github.com/jgarff/rpi_ws281x.git
           cd rpi_ws281x
           scons
           cd python
           sudo python3.6 setup.py install
 https://learn.adafruit.com/neopixels-on-raspberry-pi/software
 Apple Homekit API Call Order
 User changes light settings on iOS device
 Changing Brightness - State - Hue - Brightness
 Changing Color      - Saturation - Hue
 Changing Temp/Sat   - Saturation - Hue
 Changing State      - State
"""

def get_bridge(driver):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, 'Bridge')
    fifty_fifty = FiftyFiftyHomeKit(driver, 'Fifty fifty')
    bridge.add_accessory(fifty_fifty)

    return bridge


def get_accessory(driver):
    """Call this method to get a standalone Accessory."""
    return FiftyFiftyHomeKit(driver, 'Simple Led Strip')


# Start the accessory on port 51826
driver = AccessoryDriver(port=51826)

# Change `get_accessory` to `get_bridge` if you want to run a Bridge.
driver.add_accessory(accessory=get_accessory(driver))

# We want SIGTERM (terminate) to be handled by the driver itself,
# so that it can gracefully stop the accessory, server and advertising.
signal.signal(signal.SIGTERM, driver.signal_handler)

# Start it!
driver.start()


