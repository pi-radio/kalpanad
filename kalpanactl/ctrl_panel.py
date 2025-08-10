#!/usr/bin/env python3
import sys

from pathlib import Path

import numpy as np

from matplotlib.figure import Figure

import panel as pn

import rpyc

pn.extension(sizing_mode="stretch_width")

class KalpanaWebPanel:
    def __init__(self):
        self.conn = rpyc.connect('localhost', 37000)
    
        ACCENT="goldenrod"
        LOGO="assets/pi-radio.png"
        data = np.random.normal(1, 1, size=100)
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.hist(data, bins=20, color=ACCENT)

        a_LO = pn.widgets.EditableFloatSlider(
            value=self.srv.get_a_LO()/1e9,
            step=0.1,
            start=0.4,
            end=4.4,
            fixed_start= 0.4,
            fixed_end= 4.4,
            format="0.000000",
            disabled=False,
            name="Frequency A (GHz)")

        b_LO = pn.widgets.EditableFloatSlider(
            value=self.srv.get_b_LO()/1e9,
            step=0.1,
            start=0.4,
            end=4.4,
            fixed_start= 0.4,
            fixed_end= 4.4,
            format="0.000000",
            disabled=False,
            name="Frequency B (GHz)")

        tx_i_gain = pn.widgets.EditableFloatSlider(
            value=self.srv.get_i_gain('tx'),
            step=0.01,
            start=-0.5,
            end=0.5,
            fixed_start= -0.5,
            fixed_end= 0.5,
            format="0.00",
            disabled=False,
            name="Channel TX: I over Q  gain (dB) for sideband suppression")

        rx_i_gain = pn.widgets.EditableFloatSlider(
            value=self.srv.get_i_gain('rx'),
            step=0.01,
            start=-0.5,
            end=0.5,
            fixed_start= -0.5,
            fixed_end= 0.5,
            format="0.00",
            disabled=False,
            name="Channel RX: I over Q  gain (dB) for sideband suppression")

        tx_i_dc_offset = pn.widgets.EditableFloatSlider(
            value=self.srv.get_dc_offset('I', 'tx'),
            step=1,
            start=-200,
            end=200,
            fixed_start= -200,
            fixed_end= 200,
            format="000",
            disabled=False,
            name="Channel TX: I DC offset (mV) for LO suppression")

        tx_q_dc_offset = pn.widgets.EditableFloatSlider(
            value=self.srv.get_dc_offset('Q', 'tx'),
            step=1,
            start=-200,
            end=200,
            fixed_start= -200,
            fixed_end= 200,
            format="000",
            disabled=False,
            name="Channel TX: Q DC offset (mV) for LO suppression")

        rx_i_dc_offset = pn.widgets.EditableFloatSlider(
            value=self.srv.get_dc_offset('I', 'rx'),
            step=1,
            start=-200,
            end=200,
            fixed_start= -200,
            fixed_end= 200,
            format="000",
            disabled=False,
            name="Channel RX: I DC offset (mV) for LO suppression")

        rx_q_dc_offset = pn.widgets.EditableFloatSlider(
            value=self.srv.get_dc_offset('Q', 'rx'),
            step=1,
            start=-200,
            end=200,
            fixed_start= -200,
            fixed_end= 200,
            format="000",
            disabled=False,
            name="Channel RX: Q DC offset (mV) for LO suppression")
        
        tx_phase_offset = pn.widgets.EditableFloatSlider(
            value=self.srv.get_phase_offset('tx'),
            step=0.1,
            start=-2.5,
            end=2.5,
            fixed_start= -2.5,
            fixed_end= 2.5,
            format="0.00",
            disabled=False,
            name="Channel TX: IQ Phase offset (degrees) for sideband suppression")
        
        rx_phase_offset = pn.widgets.EditableFloatSlider(
            value=self.srv.get_phase_offset('rx'),
            step=0.1,
            start=-2.5,
            end=2.5,
            fixed_start= -2.5,
            fixed_end= 2.5,
            format="0.00",
            disabled=False,
            name="Channel RX: IQ Phase offset (degrees) for sideband suppression")


        
        GPIO2 = pn.widgets.Checkbox(name="Use Internal Reference", value=self.srv.get_gpio(2))
        GPIO3 = pn.widgets.Checkbox(name="Use Internal Reference for Low Side", value=self.srv.get_gpio(3))
        GPIO6 = pn.widgets.Checkbox(name="Disable Input 20dB Attenuator", value=self.srv.get_gpio(6))

        reset_lmx = pn.widgets.Button(name="Reset LMX", button_type="primary")
        
        pn.bind(self.update_freq, lo="a", freq=a_LO, watch=True)
        pn.bind(self.update_freq, lo="b", freq=b_LO, watch=True)


        pn.bind(self.update_i_gain, channel="tx", v=tx_i_gain, watch=True)
        pn.bind(self.update_i_gain, channel="rx", v=rx_i_gain, watch=True)

        pn.bind(self.update_dc_offset, iq='I', channel="tx", v=tx_i_dc_offset, watch=True)
        pn.bind(self.update_dc_offset, iq='Q', channel="tx", v=tx_q_dc_offset, watch=True)
        pn.bind(self.update_dc_offset, iq='I', channel="rx", v=rx_i_dc_offset, watch=True)
        pn.bind(self.update_dc_offset, iq='Q', channel="rx", v=rx_q_dc_offset, watch=True)

        pn.bind(self.update_phase_offset, channel="tx", v=tx_phase_offset, watch=True)
        pn.bind(self.update_phase_offset, channel="rx", v=rx_phase_offset, watch=True)
        
        component = pn.Accordion(
            ( "Frequency", pn.Column(a_LO, b_LO) ),
            ( "TX-side IQ Impairments (Sideband Suppression)", pn.Column (tx_i_gain, tx_phase_offset)),
            ( "TX-side DC Offsets (LO Suppression)", pn.Column (tx_i_dc_offset, tx_q_dc_offset)),
            ( "RX-side IQ Impairments (Sideband Suppression)", pn.Column (rx_i_gain, rx_phase_offset)),
            ( "RX-side DC Offsets (LO Suppression)", pn.Column (rx_i_dc_offset, rx_q_dc_offset))
        )

        sidebar = pn.pane.image.PNG(LOGO, link_url="https://pi-rad.io/")

        self.t = pn.template.FastListTemplate(
            title="Kalpana", sidebar=[sidebar], main=[component], accent=ACCENT
        ).servable()

    @property
    def srv(self):
        try:
            self.conn.root.keep_alive()
        except EOFError:
            self.conn = rpyc.connect('localhost', 37000)
            return self.srv

        return self.conn.root
        
    def update_freq(self, lo, freq):
            print(f"Updating frequency for {lo} to {freq}...")
            if lo == "a":
                self.srv.set_a_LO(freq * 1e9)
            elif lo == "b":
                self.srv.set_b_LO(freq * 1e9)
        
    def update_i_gain(self, channel, v):
        self.srv.set_i_gain(channel, v)

    def update_dc_offset(self, iq, channel, v):
        self.srv.set_dc_offset(iq, channel, v)
        
    def update_phase_offset(self, channel, v):
        self.srv.set_phase_offset(channel, v)
    
    def reset_lmx(self):
        self.srv.reset_lmx()

        
if __name__ == '__main__':
    p = KalpanaWebPanel()
    pn.serve(p.t, show=False, port=5006, static_dirs={'assets': f'{Path(__file__).parent/"assets"}'})
