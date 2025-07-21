#!/usr/bin/env python3
import click
import rpyc
import os
import time
import threading

from pathlib import Path
from json import JSONEncoder

from curiectl import Curie
from flask import Flask, request

curie = Curie()

flask_app = Flask("curiectld")

@flask_app.route("/")
def hello():
    return "Rest API"

@flask_app.route("/a_lo", methods=[ "GET", "POST", "PUT" ])
def flask_a_lo():
    if 'freq' in request.args:
        try:
            new_freq = float(request.args.get('freq'))
            
            curie.set_a_LO(new_freq)
        except:
            return f"Failed to set new frequency {e}"

    d = { 'frequency': curie.get_a_LO() }
        
    return JSONEncoder().encode(d)

@flask_app.route("/b_lo", methods=[ "GET", "POST", "PUT" ])
def flask_b_lo():
    if 'freq' in request.args:
        try:
            new_freq = float(request.args.get('freq'))
            
            curie.set_b_LO(new_freq)
        except:
            return f"Failed to set new frequency {e}"
        
    d = { 'frequency': curie.get_b_LO() }
        
    return JSONEncoder().encode(d)


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
    def get_b_LO(self):
        return curie.get_b_LO()

    @rpyc.exposed
    def get_a_LO(self):
        return curie.get_a_LO()
    
    @rpyc.exposed
    def set_b_LO(self, f):
        print(f"Setting B LO to {f}")
        curie.set_b_LO(f)

    @rpyc.exposed
    def set_a_LO(self, f):
        print(f"Setting A LO to {f}")
        curie.set_a_LO(f)

    @rpyc.exposed
    def get_gpio(self, chan):
        print(f"Get GPIO {chan} {curie.get_gpio(chan)}")
        return curie.get_gpio(chan)
        
    @rpyc.exposed
    def set_gpio(self, chan, v):
        print(f"Setting GPIO {chan} to {v}")
        curie.set_gpio(chan, v)

    @rpyc.exposed
    def reset_lmx(self, chan, v):
        print(f"Resetting LMX(s)")
        curie.reset_lmx()
        
        
        
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
