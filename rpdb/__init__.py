"""Remote Python Debugger (pdb wrapper)."""

__author__ = "Bertrand Janin <b@janin.com>"
__version__ = "0.1.6"

import pdb
import socket
import threading
import signal
import sys
import traceback
from functools import partial

DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 4444


class FileObjectWrapper(object):
    def __init__(self, fileobject, stdio):
        self._obj = fileobject
        self._io = stdio

    def __getattr__(self, attr):
        if hasattr(self._obj, attr):
            attr = getattr(self._obj, attr)
        elif hasattr(self._io, attr):
            attr = getattr(self._io, attr)
        else:
            raise AttributeError("Attribute %s is not found" % attr)
        return attr


def finally_shutdown(owner, method):
    """Wrapper to a clean-up happens after `method` is called."""
    def _wrapper(*args, **kwargs):
        """Clean-up after calling method."""
        try:
            return method(*args, **kwargs)
        finally:
            owner.shutdown()
    return _wrapper


class Rpdb(object):
    """Wrap a Pdb object with a remote session."""

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT):
        # Backup stdin and stdout before replacing them by the socket handle
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        self.port = port

        # Open a 'reusable' socket to let the webapp reload on the same port
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.skt.bind((addr, port))
        self.skt.listen(1)

        # Writes to stdout are forbidden in mod_wsgi environments
        try:
            sys.stderr.write("pdb is running on %s:%d\n"
                             % self.skt.getsockname())
        except IOError:
            pass

        self._pdb = None

    def start_debugger(self):
        """Accept external connections and run Pdb."""
        (clientsocket, address) = self.skt.accept()
        handle = clientsocket.makefile('rw')
        self._pdb = pdb.Pdb(completekey='tab',
                            stdin=FileObjectWrapper(handle, self.old_stdin),
                            stdout=FileObjectWrapper(handle, self.old_stdout))
        # wrap the methods that need extra logic
        for method in ('do_continue', 'do_c', 'do_cont',
                       'do_quit', 'do_exit', 'do_q',
                       'do_EOF'):
            setattr(self._pdb, method, finally_shutdown(self, getattr(self._pdb, method)))

        sys.stdout = sys.stdin = handle
        self.handle = handle
        OCCUPIED.claim(self.port, self.handle)

    def shutdown(self):
        """Revert stdin and stdout, close the socket."""
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        self.handle.close()
        OCCUPIED.unclaim(self.port)
        self.skt.shutdown(socket.SHUT_RDWR)
        self.skt.close()

    def __getattr__(self, name):
        """Pass on requests to the Pdb object."""
        if hasattr(self._pdb, name):
            return getattr(self._pdb, name)
        return self.__getattribute__(self, name)


def set_trace(addr=DEFAULT_ADDR, port=DEFAULT_PORT, frame=None):
    """Wrapper function to keep the same import x; x.set_trace() interface.

    We catch all the possible exceptions from pdb and cleanup.

    """
    try:
        debugger = Rpdb(addr=addr, port=port)
        debugger.start_debugger()
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
    debugger.start_debugger()
    debugger.reset()
    debugger.interaction(None, tb)


class OccupiedPorts(object):
    """Maintain rpdb port versus stdin/out file handles.

    Provides the means to determine whether or not a collision binding to a
    particular port is with an already operating rpdb session.

    Determination is according to whether a file handle is equal to what is
    registered against the specified port.
    """

    def __init__(self):
        self.lock = threading.RLock()
        self.claims = {}

    def claim(self, port, handle):
        self.lock.acquire(True)
        self.claims[port] = id(handle)
        self.lock.release()

    def is_claimed(self, port, handle):
        self.lock.acquire(True)
        got = (self.claims.get(port) == id(handle))
        self.lock.release()
        return got

    def unclaim(self, port):
        self.lock.acquire(True)
        del self.claims[port]
        self.lock.release()

# {port: sys.stdout} pairs to track recursive rpdb invocation on same port.
# This scheme doesn't interfere with recursive invocations on separate ports -
# useful, eg, for concurrently debugging separate threads.
OCCUPIED = OccupiedPorts()
