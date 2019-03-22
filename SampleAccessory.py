#!/usr/bin/env python3

import os.path
import logging


from homekit import AccessoryServer
from homekit.model import Accessory, LightBulbService
from homekit.model.characteristics import BrightnessCharacteristicMixin, BrightnessCharacteristic, HueCharacteristic


if __name__ == '__main__':
    # setup logger
    logger = logging.getLogger('accessory')
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    logger.info('starting')

    try:
        httpd = AccessoryServer(os.path.expanduser('./demoserver.json'), logger)
        httpd.set_identify_callback(lambda)

        accessory = Accessory('Light', 'PheonixFi', 'Demoserver', '0001', '0.1')

        lightService = LightBulbService()
        # lightService.set_get_value_callback();
        lightService.append_characteristic(BrightnessCharacteristic(12345678901))
        # lightService.append_characteristic(HueCharacteristic(12345678902))
        accessory.services.append(lightService)
        httpd.add_accessory(accessory)

        httpd.publish_device()
        print('published device and start serving')

        httpd.serve_forever()


    except KeyboardInterrupt:
        print('unpublish device')
        httpd.unpublish_device()
