from periphery import SPI

import math

class LMX2820:
    VCO_MIN = 5.65e9
    VCO_MAX = 11.3e9

    # Not a big deal for Kalpana out of the gate,
    # as the smallest N would be > 36 for any 
    # LMX we're using at 10MHz
    # With external 100MHz references this becomes an
    # issue, however
    MIN_N = {
        1: [ 12, 18, 19, 24 ],
        2: [ 14, 21, 22, 26 ],
        3: [ 16, 23, 24, 26 ],
        4: [ 16, 26, 27, 29 ],
        5: [ 18, 28, 29, 31 ],
        6: [ 18, 30, 31, 33 ],
        7: [ 20, 33, 34, 36 ]
    }

    VCO_GAINS = {
        1: [ 84, 115 ],
        2: [ 94, 131 ],
        3: [ 123, 156 ],
        4: [ 132, 169 ],
        5: [ 131, 163 ],
        6: [ 152, 185 ],
        7: [ 130, 151 ]
    }

    VCO_BOUNDARIES = [ 5.65e9, 6.35e9, 7.3e9, 8.1e9, 9e9, 9.8e9, 10.6e9, 11.3e9 ]

    VCO_LIMITS = [ (0,0) ] + [ (lo, hi) for lo, hi in zip(VCO_BOUNDARIES[:-1], VCO_BOUNDARIES[1:]) ]
    
    def __init__(self, spi, f_in=10e6, f_outa=10e9, pwra=3):
        self.init_regs_to_reset()

        self._spi = spi
        self._f_in = f_in

        self.set_fout(f_outa)

    @property
    def f_pfd(self):
        retval = self._f_in

        if self._osc_2x:
            retval *= 2

        retval /= self._pll_r_pre
            
        assert not (self._osc_2x and self._mult != 1)

        if self._mult != 1:
            retval *= self._mult

        retval /= self._pll_r
            
        return retval

    @property
    def fout(self):
        return self._fout

    def set_fout(self, a, b=None):
        #print(f"Setting VCO to {a}")
        f_vco = a
        enable_doubler = False
        
        if f_vco > self.VCO_MAX:
            f_vco /= 2
            self._outa_mux = 2
            #print(f"Enabling doubler {a} {f_vco}")
        elif f_vco < self.VCO_MIN:
            d = self.VCO_MIN / f_vco

            self._outa_mux = 0
            self._chdiva = math.ceil(math.log2(d)) - 1
            f_vco = a * 2**(self._chdiva + 1)
            #print(f"Setting chdiv to {self._chdiva} {d}")
        else:
            self._outa_mux = 1
            
        # TODO: Add VCO selection based on MIN_N
            
        # Bypass multiplier -- only needed for integer spurs
        self._mult = 1

        m = f_vco / self.f_pfd

        self._plln = int(m)
        
        if m == int(m):
            self._pll_num = 0
            self._pll_den = 0x3E8
            self._mash_order = 0
        else:
            # Add checks for small odd multiples
            
            f = int((m % 1) * (2**32))

            gcd = math.gcd(f, 2**32)
            
            self._pll_num = int(f / gcd)
            self._pll_den = int(2**32 / gcd)

            if self._pll_den < 7:
                self._mash_order = 1
            elif self._pll_den & 1:
                self._mash_order = 2
            else:
                self._mash_order = 3

        self._vco_sel = self.get_vco(f_vco)
        
        self._fout = a

        
        
        print(f"VCO frequency: {f_vco} VCO no: {self._vco_sel}")
        print(f"PLL: int n: {self._plln} num: {self._pll_num} den: {self._pll_den}")
        print(f"Freq: {self.f_pfd * (self._plln + self._pll_num / self._pll_den) / (1 << (self._chdiva + 1))}")

    def get_vco(self, f):
        if f < self.VCO_LIMITS[1][0] or f > self.VCO_LIMITS[-1][1]:
            raise RuntimeException(f"Invalid VCO frequency {f}")
        
        for i, (lo, hi) in enumerate(self.VCO_LIMITS):
            if f >= lo and f <= hi:
                return i

    def get_gain(self, f):
        vco = self.get_vco(f)

        d = (f - self.VCO_LIMITS[vco][0]) / (self.VCO_LIMITS[vco][1] - self.VCO_LIMITS[vco][0])
        
        return d * (self.VCO_GAINS[vco][1] - self.VCO_GAINS[vco][0]) + self.VCO_GAINS[vco][0]
        
    def init_regs_to_reset(self):
        self._osc_2x = 1
        self._mult = 1
        self._pll_r = 1
        self._pll_r_pre = 1
        self._skip_cal = 1
        
        self._fcal_hpfd_adj = 0x0
        self._fcal_lpfd_adj = 0x0
        self._dblr_cal_en = 0x1
        
        self._fcal_en = 0x1
        self._reset = 0
        self._powerdown = 0

        self._phase_sync_en = 0x0
        self._ld_vtune_en = 0x1
        self._dblr_en = 0x0
        self._instacal_en = 0x0 

        self._cal_clk_div = 0x0
        self._instacal_dly = 25
        self._quick_recall_en = 0x0
        self._acal_cmp_dly = 0xA

        self._pfd_dly_manual = 0x0
        self._vco_daciset_force = 0x0
        self._vco_capctrl_force = 0x0
        
        self._pfd_pol = 0x0
        self._pfd_single = 0x0

        self._cpg = 0xE
        self._ld_type = 0x1

        self._ld_dly = 0x3E8

        self._tempsense_en = 0x0

        self._vco_sel = 0x7
        self._vco_capctrl = 0xBF
        self._vco_daciset = 0x12C
        
        self._vco_sel_force = 0x0
        
        self._chdiva = 0
        self._chdivb = 0

        self._loopback_en = 0
        self._extvco_div = 1
        self._extvco_en = 0

        self._mash_reset_n = 1
        self._mash_order = 2
        self._mash_seed_en = 0

        self._plln = 0x38
        self._pfd_dly = 2
        self._pll_den = 0x3E8
        self._pll_num = 0

        self._mash_seed = 0
        self._instacal_pll_num = 0

        self._extpfd_div = 1
        self._pfd_sel = 1

        self._mash_reset_cnt = 0xC350

        self._sysref_inp_fmt = 0
        self._sysref_div_pre = 4
        self._sysref_repeat_ns = 0
        self._sysref_pulse = 0
        self._sysref_en = 0
        self._sysref_repeat = 0
        self._sysref_div = 1
        self._sysref_pulse_cnt = 0
        self._jesd_dac1_ctrl = 0x3F
        self._jesd_dac2_ctrl = 0
        self._jesd_dac3_ctrl = 0
        self._jesd_dac4_ctrl = 0

        self._inpin_ignore = 0
        self._psync_inp_format = 0
        self._srout_pd = 1
        self._dblbuf_outmux_en = 0
        self._dblbuf_outbuf_en = 0
        self._dblbuf_chdiv_en = 0
        self._dblbuf_pll_en = 1 
        
        self._pinmute_pol = 0
        self._outa_pd = 0
        self._outa_mux = 1
        self._outb_pd = 1
        self._outb_mux = 1
        self._outa_pwr = 3
        self._outb_pwr = 7

        R = [ lambda: 0x0000 for i in range(123) ]

        R[0] = lambda: ((0x1 << 14) |
                        (self._skip_cal << 13) |
                        (self._fcal_hpfd_adj << 9) |
                        (self._fcal_lpfd_adj << 7) |
                        (self._dblr_cal_en << 6) |
                        (0x1 << 5) |
                        (self._fcal_en << 4) |
                        (self._reset << 1) |
                        self._powerdown)

        R[1] = lambda: ((0x15E << 6) |
                        (self._phase_sync_en << 15) |
                        (self._ld_vtune_en << 5) |
                        (self._dblr_en << 1) |
                        (self._instacal_en << 0))

        R[2] = lambda: ((1 << 15) |
                        (self._cal_clk_div << 12) |
                        (self._instacal_dly << 1) |
                        (self._quick_recall_en << 0))

        R[3] = lambda: 0x41
        R[4] = lambda: 0x4204
        R[5] = lambda: 0x3832
        R[6] = lambda: (self._acal_cmp_dly << 8) | 0x43
        R[7] = lambda: 0xC8
        R[8] = lambda: 0xC802
        R[9] = lambda: 0x5
        R[10] = lambda: ((self._pfd_dly_manual << 12) |
                         (self._vco_daciset_force << 11) |
                         (self._vco_capctrl_force << 7))
        R[11] = lambda: ((0x30 << 5) |
                         (self._osc_2x << 4) |
                         (0x2))
        R[12] = lambda: ((self._mult << 10) | 0x8)
        R[13] = lambda: ((self._pll_r << 5) | 0x18)
        R[14] = lambda: ((0x03 << 12) | self._pll_r_pre)

        R[15] = lambda: ((0x02 << 12) | (self._pfd_pol << 11) | (self._pfd_single << 9) | 0x01)

        R[16] = lambda: ((0x138 << 5) | (self._cpg << 1))

        R[17] = lambda: ((self._ld_type << 6) | (0x28 << 7))

        R[18] = lambda: self._ld_dly

        R[19] = lambda: ((0x109 << 5) | (self._tempsense_en << 3))

        R[20] = lambda: ((0x13 << 9) | (self._vco_daciset))

        R[21] = lambda: 0x1C64

        R[22] = lambda: ((self._vco_sel << 13) | (0x02 << 8) | (self._vco_capctrl))

        R[23] = lambda: ((self._vco_sel_force) | (0x881 << 1))

        R[24] = lambda: 0x0E34
        R[25] = lambda: 0x0624
        R[26] = lambda: 0x0DB0
        R[27] = lambda: 0x8001
        R[28] = lambda: 0x0639
        R[29] = lambda: 0x318C
        R[30] = lambda: 0xB18C
        R[31] = lambda: 0x0401

        R[32] = lambda: ((0x01 << 12) | (self._chdivb << 9) | (self._chdiva << 6) | 0x1)

        R[33] = lambda: 0x00

        R[34] = lambda: ((self._loopback_en << 11) | (self._extvco_div << 4) | self._extvco_en)

        R[35] = lambda: ((1 << 13) | (self._mash_reset_n << 12) | (self._mash_order << 7) | (self._mash_seed_en << 6))

        R[36] = lambda: self._plln

        R[37] = lambda: ((self._pfd_dly << 9) | 0x100)

        R[38] = lambda: self._pll_den >> 16
        R[39] = lambda: self._pll_den & 0xFFFF

        R[40] = lambda: self._mash_seed >> 16
        R[41] = lambda: self._mash_seed & 0xFFFF

        R[42] = lambda: self._pll_num >> 16
        R[43] = lambda: self._pll_num & 0xFFFF

        R[44] = lambda: self._instacal_pll_num >> 16
        R[45] = lambda: self._instacal_pll_num & 0xFFFF

        R[46] = lambda: 0x0300
        R[47] = lambda: 0x0300
        R[48] = lambda: 0x4180

        R[50] = lambda: 0x0080
        R[51] = lambda: 0x203F

        R[55] = lambda: 0x0002

        R[56] = lambda: self._extpfd_div
        R[57] = lambda: self._pfd_sel

        R[59] = lambda: 0x1388
        R[60] = lambda: 0x01F4
        R[61] = lambda: 0x03E8

        R[62] = lambda: self._mash_reset_cnt >> 16
        R[63] = lambda: self._mash_reset_cnt & 0xFFFF

        R[64] = lambda: ((0x10 << 10) |
                         (self._sysref_inp_fmt << 8) |
                         (self._sysref_div_pre << 5) | 
                         (self._sysref_repeat_ns << 4) |
                         (self._sysref_pulse << 3) |
                         (self._sysref_en << 2) |
                         (self._sysref_repeat << 1))

        R[65] = lambda: self._sysref_div

        R[66] = lambda: (self._jesd_dac2_ctrl << 6) | (self._jesd_dac1_ctrl)
        R[67] = lambda: (self._sysref_pulse_cnt << 12) | (self._jesd_dac4_ctrl << 6) | self._jesd_dac3_ctrl

        R[68] = lambda: (self._inpin_ignore << 5) | (self._psync_inp_format)
        R[69] = lambda: (self._srout_pd << 4) | 0x01
        R[70] = lambda: ((self._dblbuf_outmux_en << 7) |
                         (self._dblbuf_outbuf_en << 6) |
                         (self._dblbuf_chdiv_en << 6) |
                         (self._dblbuf_pll_en << 6) |
                         0xE)

        R[77] = lambda: ((0x3 << 9) |
                         (self._pinmute_pol << 8) |
                         0xCC)
        R[78] = lambda: ((self._outa_pd << 4) |
                         (self._outa_mux))
        R[79] = lambda: ((self._outb_pd << 8) |
                         (self._outb_mux << 4) |
                         (self._outa_pwr << 1))
        R[80] = lambda: ((self._outb_pwr << 6))

        R[83] = lambda: 0xF00

        R[84] = lambda: 0x40
        R[86] = lambda: 0x40
        R[87] = lambda: 0xFF00
        R[88] = lambda: 0x3FF

        R[93] = lambda: 0x1000

        R[96] = lambda: 0x17F8
        R[98] = lambda: 0x1C80
        R[99] = lambda: 0x19B9
        R[100] = lambda: 0x533
        R[101] = lambda: 0x3E8
        R[102] = lambda: 0x28
        R[103] = lambda: 0x14
        R[104] = lambda: 0x14
        R[105] = lambda: 0xA

        R[110] = lambda: 0x1F
        R[112] = lambda: 0xFFFF

        self._R = R

        class LMX2820Regs:
            def __getitem__(regs, i):
                return self._R[i]()

        self._regs = LMX2820Regs()

    @property
    def regs(self):
        return self._regs

    def program_register(self, i):
        v = self.regs[i] | (i << 16)
        data = [ (v >> i) & 0xFF for i in [ 16, 8, 0 ] ]
        miso = self._spi.transfer(data)
        

    def reset(self):
        self._reset = 1

        self.program_register(0)

        self._reset = 0

        self.program_register(0)
        
    def program(self):
        r = self.regs

        for i in range(112, -1, -1):
            self.program_register(i)
        
    
if __name__ == '__main__':
    lmx = LMX2820(None)

    regs = lmx.regs
    
    for i in range(112, -1, -1):
        print(f"R{i}\t0x{i:02x}{regs[i]:04x}")
