""" just __init__ """
from functools import partial
import signal
import socket
import sys
import traceback

from .arpdb import ARpdb
from .rpdb import Rpdb, OCCUPIED

DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 4444


def set_trace(addr=DEFAULT_ADDR, port=DEFAULT_PORT, frame=None, active=False):
    """Wrapper function to keep the same import x; x.set_trace() interface.

    We catch all the possible exceptions from pdb and cleanup.

    if active==True, then rpdb connects to host port, instead of passively wait
    for connection (which is useless in threaded applications)

    """
    try:
        if active:
            debugger = ARpdb(addr=addr, port=port)
        else:
            debugger = Rpdb(addr=addr, port=port)
    except socket.error:
        if OCCUPIED.is_claimed(port, sys.stdout):
            # rpdb is already on this port - good enough, let it go on:
            sys.stdout.write("(Recurrent rpdb invocation ignored)\n")
            return
        else:
            # Port occupied by something else.
            raise
    try:
        debugger.set_trace(frame or sys._getframe().f_back)
    except Exception:
        traceback.print_exc()


def _trap_handler(addr, port, signum, frame):
    set_trace(addr, port, frame=frame)


def handle_trap(addr=DEFAULT_ADDR, port=DEFAULT_PORT):
    """Register rpdb as the SIGTRAP signal handler"""
    signal.signal(signal.SIGTRAP, partial(_trap_handler, addr, port))


def post_mortem(addr=DEFAULT_ADDR, port=DEFAULT_PORT):
    debugger = Rpdb(addr=addr, port=port)
    type, value, tb = sys.exc_info()
    traceback.print_exc()
    debugger.reset()
    debugger.interaction(None, tb)
