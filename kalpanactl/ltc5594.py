from periphery import SPI
import sys


def reg_property(n, start_bit=0, bit_len=8):
    mask = (1 << bit_len) - 1
    class reg_obj:
        def __get__(self, obj, objtype=None):
            return (obj.regs[n] >> start_bit) & mask

        def __set__(self, obj, value):
            print(f"{obj} {value:x}")
            sys.stdout.flush()
            obj.regs[n] = (obj.regs[n] &
                           ~(mask << start_bit) |
                           ((value & mask) << start_bit))
            obj.dirty[n] = True

    return reg_obj()
                           
class LTC5594:
    REG_LVCM_CF1 = 0x12
    REG_BAND = 0x13
    REG_CTRL = 0x16
    REG_CID = 0x17
    REG_AMP = 0x15
    
    def __init__(self, spidev):
        self.spidev = spidev

        self.regs = [ self.read_reg(i) for i in range(0x18) ]
        self.dirty = [ True ] * 0x18

        self.regs = [ 0 ] * 0x18
        self._default_regs()

    im3qy = reg_property(0x00)
    im3qx = reg_property(0x01)
    im3iy = reg_property(0x02)
    im3ix = reg_property(0x03)
    im2qx = reg_property(0x04)
    im2ix = reg_property(0x05)
    hd3qy = reg_property(0x06)
    hd3qx = reg_property(0x07)
    hd3iy = reg_property(0x08)
    hd3ix = reg_property(0x09)
    hd2qy = reg_property(0x0A)
    hd2qx = reg_property(0x0B)
    hd2iy = reg_property(0x0C)
    hd2ix = reg_property(0x0D)
    dcoi = reg_property(0x0E)
    dcoq = reg_property(0x0F)

    ip3ic = reg_property(0x10, 0, 3)
    ip3cc = reg_property(0x11, 0, 2)

    gerr = reg_property(0x11, 2, 6)
    cf1 = reg_property(0x12, 0, 5)
    lvcm = reg_property(0x12, 5, 3)
    cf2 = reg_property(0x13, 0, 5)
    lf = reg_property(0x13, 5, 2)
    band = reg_property(0x13, 7, 1)
    
    ampic = reg_property(0x14, 0, 2)
    ampcc = reg_property(0x14, 2, 2)
    ampg = reg_property(0x14, 4, 3)

    edem = reg_property(0x16, 7, 1)
    edc = reg_property(0x16, 6, 1)
    eadj = reg_property(0x16, 5, 1)
    eamp = reg_property(0x16, 4, 1)

    sdo_mode = reg_property(0x16, 2, 1)
    
    @property
    def phase(self):
        return (self.regs(0x14) << 1) | (self.regs(0x15) >> 7)

    @phase.setter
    def phase(self, v):
        self.regs[0x14] = v >> 1
        self.regs[0x15] = (self.regs[0x15] & 0x7F) | ((v & 1) << 7)
    
    def _default_regs(self):
        # Boot-up defaults
        self.ampcc = 2
        self.ampic = 2
        self.ampg = 6
        self.band = 1
        self.cf1 = 8
        self.cf2 = 3
        self.dcoi = 0x80
        self.dcoq = 0x80
        self.eadj = 1
        self.eamp = 1
        self.edc = 1
        self.edem = 1
        self.gerr = 0x20
        self.hd2ix = 0x80
        self.hd2iy = 0x80
        self.hd2qx = 0x80
        self.hd2qy = 0x80
        self.hd3ix = 0x80
        self.hd3iy = 0x80
        self.hd3qx = 0x80
        self.hd3qy = 0x80
        self.im2ix = 0x80
        self.im2qx = 0x80
        self.im3ix = 0x80
        self.im3qx = 0x80
        self.im3iy = 0x80
        self.im3qy = 0x80

        self.ip3cc = 0x02
        self.ip3ic = 0x04

        self.lf1 = 0x03
        self.lvcm = 0x02
        self.pha = 0x100
        self.sdo_mode = 0

    def set_freq(self, freq):
        print(f"LTC5594 being configured for Frequency {freq}")
        sys.stdout.flush()

        if freq < 339e6:
            self.band = 0
            self.cf1 = 31
            self.lf1 = 3
            self.cf2 = 31
        elif freq < 398e6:
            self.band = 0
            self.cf1 = 21
            self.lf1 = 3
            self.cf2 = 24
        elif freq < 419e6:
            self.band = 0
            self.cf1 = 14
            self.lf1 = 3
            self.cf2 = 23
        elif freq < 556e6:
            self.band = 0
            self.cf1 = 17
            self.lf1 = 2
            self.cf2 = 31
        elif freq < 625e6:
            self.band = 0
            self.cf1 = 10
            self.lf1 = 2
            self.cf2 = 23
        elif freq < 801e6:
            self.band = 0
            self.cf1 = 15
            self.lf1 = 1
            self.cf2 = 31
        elif freq < 831e6:
            self.band = 0
            self.cf1 = 14
            self.lf1 = 1
            self.cf2 = 27
        elif freq < 1046e6:
            self.band = 0
            self.cf1 = 8
            self.lf1 = 1
            self.cf2 = 21
        elif freq < 1242e6:
            self.band = 1
            self.cf1 = 31
            self.lf1 = 3
            self.cf2 = 31
        elif freq < 1411e6:
            self.band = 1
            self.cf1 = 21
            self.lf1 = 3
            self.cf2 = 28
        elif freq < 1696e6:
            self.band = 1
            self.cf1 = 17
            self.lf1 = 2
            self.cf2 = 26
        elif freq < 2070e6:
            self.band = 1
            self.cf1 = 15
            self.lf1 = 1
            self.cf2 = 31
        elif freq< 2470e6:
            self.band = 1
            self.cf1 = 8
            self.lf1 = 1
            self.cf2 = 21
        elif freq < 2980e6:
            self.band = 1
            self.cf1 = 2
            self.lf1 = 1
            self.cf2 = 10
        elif freq < 3500e6:
            self.band = 1
            self.cf1 = 1
            self.lf1 = 0
            self.cf2 = 19
        else:
            self.band = 1
            self.cf1 = 0
            self.lf1 = 0
            self.cf2 = 0

    def set_i_gain(self, gain):
        pass

    def set_dc_offset(self, iq, offset):
        pass

    def set_i_phase_offset(self, offset):
        pass
            
    def program(self):
        for i, d in enumerate(self.dirty):
            if not d:
                continue

            self.write_reg(i, check=False)
            self.dirty[i] = False

        sys.stdout.flush()
                                   
    def dump_regs(self):
        for i in range(0x18):
            v = self.read_reg(i)
            output.print(f"{i}: {v:02x}")
            
    def read_reg(self, reg_no : int):
        assert(reg_no < 0x18)
        r = self.spidev.transfer([ 0x80 | reg_no, 0 ])

        return r[1]

    def write_reg(self, reg_no : int, check=False):
        print(f"{reg_no:x} {self.regs[reg_no]:x}")
        sys.stdout.flush()
        assert(reg_no < 0x18)
        r = self.spidev.transfer([ reg_no, self.regs[reg_no] ])
        self.dirty[reg_no] = False

        if check and reg_no != 0x16:
           vr = self.read_reg(reg_no)
           assert vr == self.regs[reg_no], f"Mismatch: {reg_no:x}: sent {self.regs[reg_no]:x} got {vr:x}"
        
        return r[1]

