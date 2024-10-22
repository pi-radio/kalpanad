from dataclasses import dataclass
from pathlib import Path
from json import JSONDecodeError

from periphery import SPI, GPIO

from marshmallow import Schema, fields, post_load

from .lmx2820 import LMX2820
from .ltc2668 import LTC2668
from .ltc5594 import LTC5594
from .adrf6520 import ADRF6520
from .channel_gain import ADRFGainTable


@dataclass
class CurieConfig:
    f_low_lo : float = 1e9
    f_high_lo : float = 10e9
    
    rx0_gain : float = 30
    rx1_gain : float = 30
    tx0_gain : float = 30
    tx1_gain : float = 30
    
    
    I0_bias : float = 0.181
    Q0_bias : float = -0.071
    I1_bias : float = 0.182
    Q1_bias : float = -0.048
    

class CurieConfigSchema(Schema):
    f_high_lo = fields.Float()
    f_low_lo = fields.Float()
    I0_bias = fields.Float()
    Q0_bias = fields.Float()
    I0_bias = fields.Float()
    Q0_bias = fields.Float()
    rx0_gain = fields.Float()
    rx1_gain = fields.Float()
    tx0_gain = fields.Float()
    tx1_gain = fields.Float()

    @post_load
    def make_config(self, data, **kwargs):
        return CurieConfig(**data)
    

class Curie:
    iq_map = {
        (0, 'I'): 2,
        (0, 'Q'): 0,
        (1, 'I'): 3,
        (1, 'Q'): 1
    }

    gain_map = {
        ('rx', 0) : 5,
        ('rx', 1) : 6,
        ('tx', 0) : 7,
        ('tx', 1) : 8,
    }
    
    def __init__(self):
        self.load_config()

        print(self._config)
        
        self.GPIO2 = GPIO("/dev/gpiochip0", 2, "out")
        self.GPIO3 = GPIO("/dev/gpiochip0", 3, "out")
        self.GPIO6 = GPIO("/dev/gpiochip0", 6, "out")

        # /dev/spidev1.0    -- LTC5594 TX0
        # /dev/spidev1.1    -- LTC5594 TX1
        # /dev/spidev1.2    -- ADRF RX0
        # /dev/spidev1.3    -- ADRF RX1
        # /dev/spidev1.4    -- ADRF TX0
        # /dev/spidev1.5    -- ADRF TX1

        self.ltc5594 = [
            LTC5594(SPI("/dev/spidev1.0", 0, 1000000)),
            LTC5594(SPI("/dev/spidev1.1", 0, 1000000))
        ]

        self.ltc5594[0].program()
        self.ltc5594[1].program()

        self.adrf = {
            'rx0': ADRF6520(SPI("/dev/spidev1.2", 0, 1000000)),
            'rx1': ADRF6520(SPI("/dev/spidev1.3", 0, 1000000)),
            'tx0': ADRF6520(SPI("/dev/spidev1.4", 0, 1000000)),
            'tx1': ADRF6520(SPI("/dev/spidev1.5", 0, 1000000))
        }

        for adrf in self.adrf.values():
            adrf.program()
        
        self.LO_HI = LMX2820(SPI("/dev/spidev1.6", 0, 1000000), f_outa=10e9, pwra=3)
        self.LO_LO = LMX2820(SPI("/dev/spidev1.7", 0, 1000000), f_outa=1e9, pwra=0)

        self.DAC = LTC2668(SPI("/dev/spidev1.8", 0, 1000000))
        
        self.GPIO2.write(True)
        self.GPIO3.write(True)
        self.GPIO6.write(True)

        self.LO_HI.set_fout(self._config.f_high_lo)
        self.LO_HI.program()

        self.LO_LO.set_fout(self._config.f_low_lo)
        self.LO_LO.program()

        self.set_mixer_bias(0, 'I', self._config.I0_bias)
        self.set_mixer_bias(0, 'Q', self._config.Q0_bias)
        self.set_mixer_bias(1, 'I', self._config.I1_bias)
        self.set_mixer_bias(1, 'Q', self._config.Q0_bias)

        
        
    def load_config(self):
        if not Path("/etc/curie.conf").exists():
            with open("/etc/curie.conf", "w") as f:
                print("Creating new configuration")
                f.write(CurieConfigSchema().dumps(CurieConfig()))

        try:
            with open("/etc/curie.conf", "r") as f:
                self._config = CurieConfigSchema().loads(f.read())
        except JSONDecodeError:
            self._config = CurieConfig()
            self.save_config()
            
                
    def save_config(self):
        with open("/etc/curie.conf", "w") as f:
            f.write(CurieConfigSchema().dumps(self._config))
        


    def get_low_LO(self):
        return self._config.f_low_lo
        

    def get_high_LO(self):
        return self._config.f_high_lo
    
    def set_high_LO(self, f):
        assert f >= 6e9 and f <= 24e9
        self.LO_HI.set_fout(f)
        self.LO_HI.program()
        self._config.f_high_lo = f

        self.save_config()

        
    def set_low_LO(self, f):
        assert f >= 400e6 and f <= 2e9
        self.LO_LO.set_fout(f)
        self.LO_LO.program()
        self._config.f_low_lo = f

        self.save_config()


    def get_gain(self, trx, no):
        assert trx in [ 'tx', 'rx' ]
        assert chan in [ 0, 1 ]
        
        if trx == 'rx':
            if no == 0:
                return self._config.rx0_gain
            elif no == 1:
                return self._config.rx1_gain
        else:
            if no == 0:
                return self._config.tx0_gain
            elif no == 1:
                return self._config.tx1_gain

    def set_gain(self, trx, no, gain):
        assert trx in [ 'tx', 'rx' ]
        assert chan in [ 0, 1 ]

        c = self.gain_map[(trx, no)]

        V = ADRFGainTable.gain_to_voltage(gain)
        
        self.DAC.setV(c, V)
        
        if trx == 'rx':
            if no == 0:
                self._config.rx0_gain = gain
            elif no == 1:
                self._config.rx1_gain = gain
        else:
            if no == 0:
                self._config.tx0_gain = gain
            elif no == 1:
                self._config.tx1_gain = gain

        self.save_config()

            
    def get_mixer_bias(self, chan, iq):
        assert chan in [ 0, 1 ]
        assert iq in [ "I", "Q" ]
        
        if chan == 0:
            if iq == "I":
                return self._config.I0_bias
            elif iq == "Q":
                return self._config.Q0_bias
        else:
            if iq == "I":
                return self._config.I1_bias
            elif iq == "Q":
                return self._config.Q1_bias

            
    def set_mixer_bias(self, chan, iq, v):
        assert chan in [ 0, 1 ]
        assert iq in [ "I", "Q" ]
        assert v >= -0.2 and v <= 0.2
        
        c = self.iq_map[(chan, iq)]

        self.DAC.setV(c, v)

        if chan == 0:
            if iq == "I":
                self._config.I0_bias = v
            elif iq == "Q":
                self._config.Q0_bias = v
        else:
            if iq == "I":
                self._config.I1_bias = v
            elif iq == "Q":
                self._config.Q1_bias = v

        self.save_config()


    def set_gain(self, trx, chan, gain):
        c = self.gain_map[(trx, chan)]

        self.DAC.setV(c, ADRFGainTable.gain_to_voltage(gain))
