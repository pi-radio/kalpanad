#!/usr/bin/env python3
import click
import rpyc
import os
import time
import threading

from pathlib import Path

from curiectl import Curie
from flask import Flask, request

curie = Curie()

flask_app = Flask("curiectld")

@flask_app.route("/")
def hello():
    return "Rest API"

@flask_app.route("/low_lo", methods=[ "GET", "PUT" ])
def flask_low_lo():
    return f"{curie.get_low_LO()}"

@flask_app.route("/high_lo", methods=[ "GET", "PUT" ])
def flask_high_lo():
    try:
        new_freq = float(request.args.get('freq'))

        curie.set_high_LO(new_freq)
    except Exception as e:
        return "Failed to set new frequency"
    
    return f"{curie.get_high_LO()}"


def launch_flask():
    flask_app.run(host="0.0.0.0", port=5111)
    

@rpyc.service
class CurieCtlService(rpyc.Service):    
    def on_connect(self, conn):
        print("Client connected")
        
    def on_disconnect(self, conn):
        print("Client disconnected")

    @rpyc.exposed
    def keep_alive(self) -> None:
        pass

    @rpyc.exposed
    def get_high_LO(self):
        return curie.get_high_LO()

    @rpyc.exposed
    def get_low_LO(self, f):
        return curie.get_low_LO()
    
    @rpyc.exposed
    def set_high_LO(self, f):
        print(f"Setting high LO to {f}")
        curie.set_high_LO(f)

    @rpyc.exposed
    def set_low_LO(self, f):
        print(f"Setting low LO to {f}")
        curie.set_low_LO(f)

    @rpyc.exposed
    def get_mixer_bias(self, chan, iq):
        return curie.get_mixer_bias(chan, iq)
        
    @rpyc.exposed
    def set_mixer_bias(self, chan, iq, v):
        print(f"Setting chan {chan} {iq} bias to {v}")
        curie.set_mixer_bias(chan, iq, v)

        
@click.command()
def curiectld():
    print("Launching control daemon")

    if not Path("/etc/curie.conf").exists():
        print("Creating new configuration")
        CurieConfig().dumps()
    
    pid = os.fork()

    if pid == 0:
        time.sleep(5)
        os.system(f"python {Path(__file__).parent / 'ctrl_panel.py'}")
        exit()

    flask_thread = threading.Thread(target=launch_flask)
    flask_thread.daemon=True
    flask_thread.start()
    
    t = rpyc.utils.server.ThreadedServer(CurieCtlService, port=37000)
    t.start()


if __name__ == '__main__':
    curiectld()
