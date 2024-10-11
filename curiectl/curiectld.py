#!/usr/bin/env python3
import click
import rpyc

from curiectl import Curie


curie = Curie()

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
    def set_high_LO(self, f):
        print(f"Setting high LO to {f}")
        curie.set_high_LO(f)

    @rpyc.exposed
    def set_low_LO(self, f):
        print(f"Setting low LO to {f}")
        curie.set_low_LO(f)

    @rpyc.exposed
    def set_mixer_bias(self, chan, iq, v):
        print(f"Setting chan {chan} {iq} bias to {v}")
        curie.set_mixer_bias(chan, iq, v)

        
@click.command()
def curiectld():
    print("Launching control daemon")

    t = rpyc.utils.server.ThreadedServer(CurieCtlService, port=37000)
    t.start()


if __name__ == '__main__':
    curiectld()
