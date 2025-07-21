#!/usr/bin/env python3
import sys

from pathlib import Path

import numpy as np

from matplotlib.figure import Figure

import panel as pn

import rpyc

pn.extension(sizing_mode="stretch_width")

class CurieWebPanel:
    def __init__(self):
        self.conn = rpyc.connect('localhost', 37000)
    
        ACCENT="goldenrod"
        LOGO="assets/pi-radio.png"
        data = np.random.normal(1, 1, size=100)
        fig = Figure(figsize=(8, 4))
        ax = fig.subplots()
        ax.hist(data, bins=20, color=ACCENT)

        a_LO = pn.widgets.EditableFloatSlider(
            value=1,
            step=0.1,
            start=0.4,
            end=4.4,
            fixed_start= 0.4,
            fixed_end= 4.4,
            format="0.000000",
            disabled=False,
            name="Frequency A (GHz)")

        b_LO = pn.widgets.EditableFloatSlider(
            value=2,
            step=0.1,
            start=0.4,
            end=4.4,
            fixed_start= 0.4,
            fixed_end= 4.4,
            format="0.000000",
            disabled=False,
            name="Frequency B (GHz)")
        
        GPIO2 = pn.widgets.Checkbox(name="Use Internal Reference", value=self.srv.get_gpio(2))
        GPIO3 = pn.widgets.Checkbox(name="Use Internal Reference for Low Side", value=self.srv.get_gpio(3))
        GPIO6 = pn.widgets.Checkbox(name="Disable Input 20dB Attenuator", value=self.srv.get_gpio(6))

        reset_lmx = pn.widgets.Button(name="Reset LMX", button_type="primary")
        
        pn.bind(self.update_freq, lo="a", freq=a_LO, watch=True)
        pn.bind(self.update_freq, lo="b", freq=b_LO, watch=True)

        
        component = pn.Accordion(
            ( "Frequency", pn.Column(a_LO, b_LO) )
        )

        sidebar = pn.pane.image.PNG(LOGO, link_url="https://pi-rad.io/")

    
        self.t = pn.template.FastListTemplate(
            title="Curie", sidebar=[sidebar], main=[component], accent=ACCENT
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
        
    
    def reset_lmx(self):
        self.srv.reset_lmx()

        
if __name__ == '__main__':
    p = CurieWebPanel()
    pn.serve(p.t, show=False, port=5006, static_dirs={'assets': f'{Path(__file__).parent/"assets"}'})
