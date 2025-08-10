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
    
    # IQ Corrections for Sideband Suppression
    tx_i_gain : float = 0
    rx_i_gain : float = 0
    tx_phase_offset : float = 0
    rx_phase_offset : float = 0

    # DC Offsets for LO suppression
    tx_i_dc_offset : float = 0
    tx_q_dc_offset : float = 0
    rx_i_dc_offset : float = 0
    rx_q_dc_offset : float = 0
   
class KalpanaConfigSchema(Schema):
    f_b_lo = fields.Float()
    f_a_lo = fields.Float()
    gpio_val = fields.Dict(fields.Int(), fields.Bool())

    # IQ Corrections for Sideband Suppression
    tx_i_gain : fields.Float()
    rx_i_gain : fields.Float()
    tx_phase_offset : fields.Float()
    rx_phase_offset : fields.Float()

    # DC Offsets for LO Suppression
    tx_i_dc_offset : fields.Float()
    tx_q_dc_offset : fields.Float()
    rx_i_dc_offset : fields.Float()
    rx_q_dc_offset : fields.Float()

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
        
        # SPI 1.0 is the TX-side LTC5594
        # SPI 1.1 is thee RX-side LTC5594
        self.ltc5594 = [
            LTC5594(SPI("/dev/spidev1.0", 0, 1000000)),
            LTC5594(SPI("/dev/spidev1.1", 0, 1000000))
        ]

        self.ltc5594[0].set_freq(self._config.f_a_lo)
        # IQ Corrections for Sideband Suppression
        self.ltc5594[0].set_i_gain(self._config.tx_i_gain)
        self.ltc5594[0].set_phase_offset(self._config.tx_phase_offset)
        # DC Offsets for LO Suppression
        self.ltc5594[0].set_dc_offset("I", self._config.tx_i_dc_offset)
        self.ltc5594[0].set_dc_offset("Q", self._config.tx_q_dc_offset)
        self.ltc5594[0].program()

        
        self.ltc5594[1].set_freq(self._config.f_b_lo)
        # IQ Corrections for Sideband Suppression
        self.ltc5594[1].set_i_gain(self._config.rx_i_gain)
        self.ltc5594[1].set_phase_offset(self._config.rx_phase_offset)
        # DC Offsets for LO Suppression
        self.ltc5594[1].set_dc_offset("I", self._config.rx_i_dc_offset)
        self.ltc5594[1].set_dc_offset("Q", self._config.rx_q_dc_offset)
        self.ltc5594[1].program()
       
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

    def get_i_gain(self, channel):
        assert channel in ['tx', 'rx']

        if channel == 'tx':
            return self._config.tx_i_gain
        else:
            return self._config.rx_i_gain

    
    def set_b_LO(self, f):
        assert f >= 400e6 and f <= 4.4e9
        print(f"Setting the B LO to {f}")

        self.GPIO[2].write(True)
        self.GPIO[3].write(True)
        time.sleep(0.01)

        self.LO_B.set_fout(f)
        self.LO_B.program()
        self._config.f_b_lo = f

        time.sleep(0.01)        
        self.GPIO[2].write(self._config.gpio_val[2])
        self.GPIO[3].write(self._config.gpio_val[3])

        print(f"Telling the RX 5594 to configure for {f}")
        self.ltc5594[1].set_freq(self._config.f_b_lo)
        self.ltc5594[1].program()
        
        self.save_config()

        
    def set_a_LO(self, f):
        assert f >= 400e6 and f <= 4.4e9
        print(f"Setting the A LO to {f}")

        self.GPIO[2].write(True)
        self.GPIO[3].write(True)
        time.sleep(0.01)

        self.LO_A.set_fout(f)
        self.LO_A.program()
        self._config.f_a_lo = f

        time.sleep(0.01)        
        self.GPIO[2].write(self._config.gpio_val[2])
        self.GPIO[3].write(self._config.gpio_val[3])

        print(f"Telling the TX 5594 to configure for {f}")
        self.ltc5594[0].set_freq(self._config.f_a_lo)
        self.ltc5594[0].program()

        self.save_config()

    # IQ Corrections for Sideband Suppression    
    def set_i_gain(self, channel, gain):
        assert channel in [ 'tx', 'rx' ]
        assert gain >= -0.5 and gain <= 0.5

        if channel == 'tx':
            ltc = self.ltc5594[0]
            self._config.tx_i_gain = gain
        else:
            ltc = self.ltc5594[1]
            self._config.rx_i_gain = gain
                    
        ltc.set_i_gain(gain)
        ltc.program()

    # IQ Corrections for Sideband Suppression
    def set_phase_offset(self, channel, offset):
        assert channel in [ 'tx', 'rx' ]
        assert offset >= -2.5 and offset <= 2.5

        if channel == 'tx':
            ltc = self.ltc5594[0]
            self._config.tx_phase_offset = offset
        else:
            ltc = self.ltc5594[1]
            self._config.rx_phase_offset = offset
                    
        ltc.set_phase_offset(offset)
        ltc.program()

    def get_phase_offset(self, channel):
        assert channel in ['tx', 'rx']
        if channel == 'tx':
            return self._config.tx_phase_offset
        else:
            return self._config.rx_phase_offset

    # DC Offsets for LO Suppression
    def set_dc_offset(self, iq, channel, offset):
        assert iq in [ 'I', 'Q' ]
        assert channel in [ 'tx', 'rx' ]
        assert offset >= -200 and offset <= 200

        if channel == 'tx':
            ltc = self.ltc5594[0]
            if iq == 'I':
                self._config.tx_i_dc_offset = offset
            else:
                self._config.tx_q_dc_offset = offset
        else:
            ltc = self.ltc5594[1]
            if iq == 'I':
                self._config.rx_i_dc_offset = offset
            else:
                self._config.rx_q_dc_offset = offset

        ltc.set_dc_offset(iq, offset)
            
        ltc.program()

    def get_dc_offset(self, iq, channel):
        assert iq in ['I', 'Q']
        assert channel in ['tx', 'rx']

        if iq == 'I' and channel == 'tx':
            return self._config.tx_i_dc_offset
        elif iq == 'I' and channel == 'rx':
            return self._config.rx_i_dc_offset
        elif iq == 'Q' and channel == 'tx':
            return self._config.tx_q_dc_offset
        else:
            return self._config.rx_q_dc_offset
     
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
