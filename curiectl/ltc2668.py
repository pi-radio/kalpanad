import time

class LTC2668:
    CMD_WRITE_CODE = 0x00
    CMD_WRITE_SPAN = 0x60
    CMD_WRITE_CODE_ALL = 0x80
    CMD_UPDATE = 0x10
    CMD_WCU = 0x30
    CMD_WCUA = 0x20
    CMD_WCAUA = 0xA0
    CMD_POWER_DOWN = 0x40
    CMD_POWER_DOWN_CHIP = 0x50
    

    
    def __init__(self, spi):
        self._spi = spi

    def setV(self, channel, V):
        code = int((V + 2.5) / 5 * 65535)

        print(f"Sending code {code:x} for {V}V...")

        self._spi.transfer([0xE0, 0x00, 0x04])
        time.sleep(0.01)
        self._spi.transfer([ self.CMD_WCU | channel, code >> 8, code & 0xFF ])
