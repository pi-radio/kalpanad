#!/usr/bin/env python3
import sys

import numpy as np

from matplotlib.figure import Figure

import panel as pn

ACCENT="goldenrod"
LOGO="pi-radio.png"

pn.extension(sizing_mode="stretch_width")

data = np.random.normal(1, 1, size=100)
fig = Figure(figsize=(8, 4))
ax = fig.subplots()
ax.hist(data, bins=20, color=ACCENT)

filter_options = [
    'bypass', '36MHz', '72MHz', '144MHz',
    '288MHz', '432MHz', '576MHz', '720MHz'
]

low_LO = pn.widgets.EditableFloatSlider(
    value=1,
    step=0.1,
    start=0.4,
    end=1.8,
    format="0.000000",
    disabled=False,
    name="Low LO Frequency (GHz)")

high_LO = pn.widgets.EditableFloatSlider(
    value=10,
    step=0.1,
    start=6.0,
    end=22.8,
    format="0.000000",
    disabled=False,
    name="High LO Frequency (GHz)")

RX0_gain = pn.widgets.EditableFloatSlider(
    value=32,
    step=0.1,
    start=0,
    end=60.0,
    format="00.0",
    disabled=False,
    name="RX0 Gain (dB)")

RX0_filter = pn.widgets.Select(
    name="RX0 Filter",
    options=filter_options)

RX1_gain = pn.widgets.EditableFloatSlider(
    value=32,
    step=0.1,
    start=0,
    end=60.0,
    format="00.0",
    disabled=False,
    name="RX1 Gain (dB)")

RX1_filter = pn.widgets.Select(
    name="RX1 Filter",
    options=filter_options)

TX0_gain = pn.widgets.EditableFloatSlider(
    value=32,
    step=0.1,
    start=0,
    end=60.0,
    format="00.0",
    disabled=False,
    name="TX0 Gain (dB)")

TX0_filter = pn.widgets.Select(
    name="TX0 Filter",
    options=filter_options)

TX1_gain = pn.widgets.EditableFloatSlider(
    value=32,
    step=0.1,
    start=0,
    end=60.0,
    format="00.0",
    disabled=False,
    name="TX1 Gain (dB)")

TX1_filter = pn.widgets.Select(
    name="TX1 Filter",
    options=filter_options)

TX0_I_bias = pn.widgets.EditableFloatSlider(
    value=0,
    step=0.001,
    start=-0.15,
    end=0.15,
    format="0.000",
    disabled=False,
    name="TX0 I bias (V)")

TX0_Q_bias = pn.widgets.EditableFloatSlider(
    value=0,
    step=0.001,
    start=-0.15,
    end=0.15,
    format="0.000",
    disabled=False,
    name="TX0 Q bias (V)")

TX1_I_bias = pn.widgets.EditableFloatSlider(
    value=0,
    step=0.001,
    start=-0.15,
    end=0.15,
    format="0.000",
    disabled=False,
    name="TX1 I bias (V)")

TX1_Q_bias = pn.widgets.EditableFloatSlider(
    value=0,
    step=0.001,
    start=-0.15,
    end=0.15,
    format="0.000",
    disabled=False,
    name="TX1 Q bias (V)")



def update_freq(lo, freq):
    print(f"Updating frequency for {channel} to {freq}...")
    
    
def update_gain(channel, gain):
    print(f"Updating gain for {channel} to {gain}...")

pn.bind(update_freq, lo="lo", freq=low_LO, watch=True)
pn.bind(update_freq, lo="hi", freq=high_LO, watch=True)
pn.bind(update_gain, channel="rx0", gain=RX0_gain, watch=True)
pn.bind(update_gain, channel="rx1", gain=RX1_gain, watch=True)
pn.bind(update_gain, channel="tx0", gain=TX0_gain, watch=True)
pn.bind(update_gain, channel="tx1", gain=TX1_gain, watch=True)


component = pn.Accordion(
    ( "Frequency", pn.Column(low_LO, high_LO) ),
    ( "Filters", pn.Column(RX0_filter, RX1_filter, TX0_filter, TX1_filter) ),
    ( "Gain", pn.Column(RX0_gain, RX1_gain, TX0_gain, TX1_gain) ),
    ( "LO Suppression", pn.Column(TX0_I_bias, TX0_Q_bias, TX1_I_bias, TX1_Q_bias) ),
    ( "Power", pn.Column("Dookie") )
)


t = pn.template.FastListTemplate(
    title="Curie", sidebar=[LOGO], main=[component], accent=ACCENT
).servable()


if __name__ == '__main__':
    pn.serve(t, show=False, port=5006)
