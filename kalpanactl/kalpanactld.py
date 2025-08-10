#!/usr/bin/env python3
import click
import rpyc
import os
import sys
import time
import threading

from pathlib import Path
from json import JSONEncoder

sys.path.insert(0, "../")
print(f"Path: {sys.path}")
from kalpanactl import Kalpana
from flask import Flask, request

kalpana = Kalpana()

flask_app = Flask("kalpanactld")

@flask_app.route("/")
def hello():
    return "Rest API"

@flask_app.route("/a_lo", methods=[ "GET", "POST", "PUT" ])
def flask_a_lo():
    if 'freq' in request.args:
        try:
            new_freq = float(request.args.get('freq'))
            
            kalpana.set_a_LO(new_freq)
        except:
            return f"Failed to set new frequency {e}"

    d = { 'frequency': kalpana.get_a_LO() }
        
    return JSONEncoder().encode(d)

@flask_app.route("/b_lo", methods=[ "GET", "POST", "PUT" ])
def flask_b_lo():
    if 'freq' in request.args:
        try:
            new_freq = float(request.args.get('freq'))
            
            kalpana.set_b_LO(new_freq)
        except:
            return f"Failed to set new frequency {e}"
        
    d = { 'frequency': kalpana.get_b_LO() }
        
    return JSONEncoder().encode(d)


def launch_flask():
    flask_app.run(host="0.0.0.0", port=5111)
    

@rpyc.service
class KalpanaCtlService(rpyc.Service):    
    def on_connect(self, conn):
        print("Client connected")
        
    def on_disconnect(self, conn):
        print("Client disconnected")

    @rpyc.exposed
    def keep_alive(self) -> None:
        pass

    @rpyc.exposed
    def get_b_LO(self):
        return kalpana.get_b_LO()

    @rpyc.exposed
    def get_a_LO(self):
        return kalpana.get_a_LO()
    
    @rpyc.exposed
    def set_b_LO(self, f):
        print(f"Setting B LO to {f}")
        kalpana.set_b_LO(f)

    @rpyc.exposed
    def set_a_LO(self, f):
        print(f"Setting A LO to {f}")
        kalpana.set_a_LO(f)

    @rpyc.exposed
    def get_gpio(self, chan):
        print(f"Get GPIO {chan} {kalpana.get_gpio(chan)}")
        return kalpana.get_gpio(chan)
        
    @rpyc.exposed
    def set_gpio(self, chan, v):
        print(f"Setting GPIO {chan} to {v}")
        kalpana.set_gpio(chan, v)

    @rpyc.exposed
    def get_i_gain(self, chan):
        return kalpana.get_i_gain(chan)
        
    @rpyc.exposed
    def get_dc_offset(self, iq, chan):
        return kalpana.get_dc_offset(iq, chan)
    
    @rpyc.exposed
    def get_phase_offset(self, chan):
        return kalpana.get_phase_offset(chan)
        
    @rpyc.exposed
    def set_i_gain(self, chan, v):
        kalpana.set_i_gain(chan, v)
        
    @rpyc.exposed
    def set_dc_offset(self, iq, chan, v):
        kalpana.set_dc_offset(iq, chan, v)

        
    @rpyc.exposed
    def set_phase_offset(self, chan, v):
        kalpana.set_phase_offset(chan, v)
        
    @rpyc.exposed
    def reset_lmx(self, chan, v):
        print(f"Resetting LMX(s)")
        kalpana.reset_lmx()
        
        
        
@click.command()
def kalpanactld():
    print("Launching control daemon")

    if not Path("/etc/kalpana.conf").exists():
        print("Creating new configuration")
        KalpanaConfig().dumps()
    
    pid = os.fork()

    if pid == 0:
        time.sleep(5)
        os.system(f"python {Path(__file__).parent / 'ctrl_panel.py'}")
        exit()

    flask_thread = threading.Thread(target=launch_flask)
    flask_thread.daemon=True
    flask_thread.start()
    
    t = rpyc.utils.server.ThreadedServer(KalpanaCtlService, port=37000)
    t.start()


if __name__ == '__main__':
    kalpanactld()
