import logging
import signal

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver


logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

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

import neopixel, board

from pyhap.accessory import Accessory
from pyhap.const import CATEGORY_LIGHTBULB


class NeoPixelLightStrip(Accessory):
    category = CATEGORY_LIGHTBULB

    def __init__(self, *args, **kwargs):

        LED_count = 50
        is_GRB = True
        LED_pin = 18,
        LED_freq_hz = 800000
        LED_DMA = 1
        LED_brightness = 255
        LED_invert = False

        """
        LED_Count - the number of LEDs in the array
        is_GRB - most neopixels are GRB format - Normal:True
        LED_pin - must be PWM pin 18 - Normal:18
        LED_freq_hz - frequency of the neopixel leds - Normal:800000
        LED_DMA - Normal:10
        LED_Brightness - overall brightness - Normal:255
        LED_invert - Normal:False
        For more information regarding these settings
            please review rpi_ws281x source code
        """

        super().__init__(*args, **kwargs)

        # Set our neopixel API services up using Lightbulb base
        serv_light = self.add_preload_service(
            'Lightbulb', chars=['On', 'Hue', 'Saturation', 'ProgramMode'])

        # Configure our callbacks
        self.char_hue = serv_light.configure_char(
            'Hue', setter_callback=self.set_hue)
        self.char_saturation = serv_light.configure_char(
            'Saturation', setter_callback=self.set_saturation)
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_state)
        # self.char_on = serv_light.configure_char(
        #     'Brightness', setter_callback=self.set_brightness)
        self.char_program_mode = serv_light.configure_char(
            'ProgramMode', setter_callback=self.set_program_mode)

        # Set our instance variables
        self.accessory_state = 0  # State of the neo light On/Off
        self.hue = 0  # Hue Value 0 - 360 Homekit API
        self.saturation = 100  # Saturation Values 0 - 100 Homekit API
        self.brightness = 100  # Brightness value 0 - 100 Homekit API
        self.char_program_mode = 0

        # self.is_GRB = is_GRB  # Most neopixels are Green Red Blue
        # self.LED_count = LED_count

        # ------------------ TESTING VARIABLES ---------------------
        self.is_GRB = True  # Most neopixels are Green Red Blue
        self.LED_count = 50
        # --------------------- END TESTING ------------------------

        self.neo_strip = neopixel.NeoPixel(board.D18, LED_count, brightness=1, pixel_order=neopixel.GRB)

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

    def set_program_mode(self, value):
        print(value)

    def update_neopixel_with_color(self, red, green, blue):
        for i in range(self.LED_count):
            if (self.is_GRB):
                self.neo_strip[i] = (int(green), int(red), int(blue))
            else:
                self.neo_strip[i] = (int(red), int(green), int(blue))
        self.neo_strip.show()

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


def get_bridge(driver):
    """Call this method to get a Bridge instead of a standalone accessory."""
    bridge = Bridge(driver, 'Bridge')
    # temp_sensor = TemperatureSensor(driver, 'Sensor 2')
    # temp_sensor2 = TemperatureSensor(driver, 'Sensor 1')
    # bridge.add_accessory(temp_sensor)
    # bridge.add_accessory(temp_sensor2)

    neopixel_one = NeoPixelLightStrip(driver, 'Pixel 1')
    bridge.add_accessory(neopixel_one)

    return bridge


def get_accessory(driver):
    """Call this method to get a standalone Accessory."""
    return NeoPixelLightStrip(driver, 'NeopixelTest')


# Start the accessory on port 51826
driver = AccessoryDriver(port=51826)

# Change `get_accessory` to `get_bridge` if you want to run a Bridge.
driver.add_accessory(accessory=get_accessory(driver))

# We want SIGTERM (terminate) to be handled by the driver itself,
# so that it can gracefully stop the accessory, server and advertising.
signal.signal(signal.SIGTERM, driver.signal_handler)

# Start it!
driver.start()
