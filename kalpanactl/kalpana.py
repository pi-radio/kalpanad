import time

from dataclasses import dataclass, field
from pathlib import Path
from json import JSONDecodeError

from periphery import SPI, GPIO

from marshmallow import Schema, fields, post_load

from .lmx2820 import LMX2820
#from .ltc2668 import LTC2668
from .ltc5594 import LTC5594
#from .adrf6520 import ADRF6520
#from .channel_gain import ADRFGainTable


@dataclass
class KalpanaConfig:
    f_a_lo : float = 1e9
    f_b_lo : float = 2e9
    gpio_val : dict = field(default_factory=lambda: { 2: True, 3: True, 6: True })

class KalpanaConfigSchema(Schema):
    f_b_lo = fields.Float()
    f_a_lo = fields.Float()
    gpio_val = fields.Dict(fields.Int(), fields.Bool())

    @post_load
    def make_config(self, data, **kwargs):
        return KalpanaConfig(**data)
    

class Kalpana:
   
    def __init__(self):
        self.load_config()

        print(self._config)
        
        self.GPIO = {
            2: GPIO("/dev/gpiochip0", 2, "out"),
            3: GPIO("/dev/gpiochip0", 3, "out"),
            6: GPIO("/dev/gpiochip0", 6, "out"),
        }
                
        self.ltc5594 = [
            LTC5594(SPI("/dev/spidev1.0", 0, 1000000)),
            LTC5594(SPI("/dev/spidev1.1", 0, 1000000))
        ]

        self.ltc5594[0].program(self._config.f_a_lo)
        self.ltc5594[1].program(self._config.f_b_lo)
       
        self.LO_B = LMX2820(SPI("/dev/spidev1.3", 0, 1000000), f_outa=2e9, pwra=3)
        self.LO_A = LMX2820(SPI("/dev/spidev1.2", 0, 1000000), f_outa=1e9, pwra=3)

        # Program GPIOs to use internal reference first
        # to make sure LMX has a ref clock
        self.set_gpio(2, True)
        self.set_gpio(3, True)
        self.set_gpio(6, self._config.gpio_val[6])
        
        self.LO_B.set_fout(self._config.f_b_lo)
        self.LO_B.program()

        self.LO_A.set_fout(self._config.f_a_lo)
        self.LO_A.program()

        self.set_gpio(2, self._config.gpio_val[2])
        self.set_gpio(3, self._config.gpio_val[3])

    def load_config(self):
        if not Path("/etc/kalpana.conf").exists():
            with open("/etc/kalpana.conf", "w") as f:
                print("Creating new configuration")
                f.write(KalpanaConfigSchema().dumps(KalpanaConfig()))

        try:
            with open("/etc/kalpana.conf", "r") as f:
                self._config = KalpanaConfigSchema().loads(f.read())
        except JSONDecodeError:
            self._config = KalpanaConfig()
            self.save_config()
            
                
    def save_config(self):
        with open("/etc/kalpana.conf", "w") as f:
            f.write(KalpanaConfigSchema().dumps(self._config))
        


    def get_a_LO(self):
        return self._config.f_a_lo
        

    def get_b_LO(self):
        return self._config.f_b_lo
    
    def set_b_LO(self, f):
        assert f >= 400e6 and f <= 4.4e9

        self.GPIO[2].write(True)
        self.GPIO[3].write(True)
        time.sleep(0.01)

        self.LO_B.set_fout(f)
        self.LO_B.program()
        self._config.f_b_lo = f

        time.sleep(0.01)        
        self.GPIO[2].write(self._config.gpio_val[2])
        self.GPIO[3].write(self._config.gpio_val[3])

        self.ltc5594[0].program(self._config.f_b_lo)
        
        self.save_config()

        
    def set_a_LO(self, f):
        assert f >= 400e6 and f <= 4.4e9

        self.GPIO[2].write(True)
        self.GPIO[3].write(True)
        time.sleep(0.01)

        self.LO_A.set_fout(f)
        self.LO_A.program()
        self._config.f_a_lo = f

        time.sleep(0.01)        
        self.GPIO[2].write(self._config.gpio_val[2])
        self.GPIO[3].write(self._config.gpio_val[3])

        self.ltc5594[1].program(self._config.f_a_lo)

        self.save_config()

    def get_gpio(self, channel):
        try:
            return self._config.gpio_val[channel]
        except KeyError:
            raise Exception(f"Invalid channel {channel}")

    def set_gpio(self, channel, v):
        try:
            gpio = self.GPIO[channel]
        except KeyError:
            raise Exception(f"Invalid channel {channel}")

        v = True if v else False
        gpio.write(v)
        self._config.gpio_val[channel] = v
        self.save_config()

    def reset_lmx(self):
        self.LO_A.reset()
        self.LO_B.reset()

        self.LO_A.program()
        self.LO_B.program()
