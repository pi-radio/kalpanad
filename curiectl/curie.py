from periphery import SPI, GPIO

from .lmx2820 import LMX2820
from .ltc2668 import LTC2668

class Curie:
    iq_map = {
        (0, 'I'): 2,
        (0, 'Q'): 0,
        (1, 'I'): 3,
        (1, 'Q'): 1
    }
    
    def __init__(self):
        self.GPIO2 = GPIO("/dev/gpiochip0", 2, "out")
        self.GPIO3 = GPIO("/dev/gpiochip0", 3, "out")
        self.GPIO6 = GPIO("/dev/gpiochip0", 6, "out")

        self.LO_HI = LMX2820(SPI("/dev/spidev1.6", 0, 1000000), f_outa=10e9, pwra=3)
        self.LO_LO = LMX2820(SPI("/dev/spidev1.7", 0, 1000000), f_outa=1e9, pwra=0)

        self.DAC = LTC2668(SPI("/dev/spidev1.8", 0, 1000000))
        
        self.GPIO2.write(True)
        self.GPIO3.write(True)
        self.GPIO6.write(True)
        
        self.LO_HI.program()
        self.LO_LO.program()

        self.set_mixer_bias(0, 'I', 0.181)
        self.set_mixer_bias(0, 'Q', -0.071)
        self.set_mixer_bias(1, 'I', 0.182)
        self.set_mixer_bias(1, 'Q', -0.048)
        
    def set_high_LO(self, f):
        assert f >= 6e9 and f <= 24e9
        self.LO_HI.set_fout(f)
        self.LO_HI.program()

    def set_low_LO(self, f):
        assert f >= 400e6 and f <= 2e9
        self.LO_LO.set_fout(f)
        self.LO_LO.program()

    def set_mixer_bias(self, chan, iq, v):
        c = self.iq_map[(chan, iq)]

        self.DAC.setV(c, v)
