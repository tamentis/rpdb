"""Remote Python Debugger (pdb wrapper)."""

__author__ = "Bertrand Janin <b@janin.com>"
__version__ = "0.2.0"

from contextlib import contextmanager
import pdb
import socket
import threading
import signal
import sys
import time
import traceback
import os
import typing as t
from functools import partial

from .ports import find_available_port

DEFAULT_ADDR = "127.0.0.1"
DEFAULT_PORT = 4444


def get_default_address():
    return os.environ.get("PYTHON_RPDB_ADDRESS", DEFAULT_ADDR)


def get_default_port():
    return int(os.environ.get("PYTHON_RPDB_PORT", DEFAULT_PORT))

def should_find_available_port():
    return os.environ.get("PYTHON_RPDB_FIND_AVAILABLE_PORT", "1") == "1"

def safe_print(msg):
    # Writes to stdout are forbidden in mod_wsgi environments
    try:
        sys.stderr.write("[rpdb] " + msg + "\n")
    except IOError:
        pass


# https://github.com/gotcha/ipdb/blob/400e37c56c9772fdc4c04ddb29d8a4a20568fb1a/ipdb/__main__.py#L233-L246
@contextmanager
def launch_ipdb_on_exception():
    try:
        yield
    except Exception:
        post_mortem()
    finally:
        pass


# iex is a concise alias
iex = launch_ipdb_on_exception()


def ipython_available():
    try:
        from IPython.core.debugger import Pdb

        return True
    except ImportError:
        return False


def get_debugger_class():
    # TODO shell = get_ipython() to detect if we are in ipython
    # from IPython.terminal.debugger import TerminalPdb

    debugger_base = pdb.Pdb

    if ipython_available():
        from IPython.core.debugger import Pdb

        debugger_base = Pdb

    class Debugger(Rpdb, debugger_base):
        def __init__(self, addr=None, port=None):
            Rpdb.__init__(self, addr=addr, port=port, debugger_base=debugger_base)

    return Debugger


def shutdown_socket(sock: socket.socket):
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass  # Socket is already closed
    finally:
        sock.close()


class FileObjectWrapper(object):
    """
    A wrapper class for file objects that provides access to both the wrapped file object and standard I/O streams.
    """

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


class Rpdb:
    def __init__(self, addr=None, port=None, debugger_base=t.Type[pdb.Pdb]):
        """Initialize the socket and initialize pdb."""

        self.debugger = debugger_base

        addr = addr or get_default_address()
        port = port or get_default_port()

        # if you have a forked application, breakpoint could be called multiple times
        # this enables you to avoid having to make sure another debugging session is not running
        if should_find_available_port():
            original_port = port
            port = find_available_port(addr, port)
            if port != original_port:
                safe_print(f"port {original_port} is in use, using {port} instead\n")

        safe_print(f"attempting to bind {addr}:{port}")

        self.dup_stdout_fileno = None
        self.dup_stdin_fileno = None

        # Backup stdin and stdout before replacing them by the socket handle
        # this seems to fail in scenarios like pytester, which creates a subprocess and mutates pipes in some way
        # this is why we have these wrapped in a try/except block.

        try:
            self.dup_stdout_fileno = os.dup(sys.stdout.fileno())
        except (AttributeError, IOError, ValueError):
            safe_print("failed to backup stdin")
            pass

        try:
            self.dup_stdin_fileno = os.dup(sys.stdin.fileno())
        except (AttributeError, IOError, ValueError):
            safe_print("failed to backup stdin")
            pass

        # Open a 'reusable' socket to let the webapp reload on the same port
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.skt.bind((addr, port))
        self.skt.listen(1)

        safe_print("running on %s:%d\n" % self.skt.getsockname())

        (clientsocket, address) = self.skt.accept()
        self.clientsocket = clientsocket
        self.port = port
        handle = clientsocket.makefile("rw")

        self.debugger.__init__(
            self,
            completekey="tab",
            stdin=handle,
            stdout=handle,
        )

        # overwrite the default stdout and stdin with the socket file handles
        # if this isn't done, any other interactive programs (like `interact` or ipy) will fail to operate
        
        if self.dup_stdout_fileno:
            os.dup2(clientsocket.fileno(), sys.stdout.fileno())
        
        if self.dup_stdin_fileno:
            os.dup2(clientsocket.fileno(), sys.stdin.fileno())

        OCCUPIED.claim(port, sys.stdout)

    def shutdown(self):
        """Revert stdin and stdout, close the socket."""
        safe_print("shutting down\n")

        # restore original stdout and stdin since we are exiting debug mode
        if self.dup_stdout_fileno:
            os.dup2(self.dup_stdout_fileno, sys.stdout.fileno())

        if self.dup_stdin_fileno:
            os.dup2(self.dup_stdin_fileno, sys.stdin.fileno())

        # `shutdown` on the `skt` will trigger an error
        # if you don't `shutdown` the `clientsocket` socat & friends will hang
        # self.clientsocket.shutdown(socket.SHUT_RDWR)
        # self.clientsocket.close()
        shutdown_socket(self.clientsocket)

        # self.skt.shutdown(socket.SHUT_RDWR)
        # self.skt.close()
        shutdown_socket(self.skt)

        OCCUPIED.unclaim(self.port)

    def do_continue(self, arg):
        """Clean-up and do underlying continue."""

        try:
            return self.debugger.do_continue(self, arg)
        finally:
            self.shutdown()

    do_c = do_cont = do_continue

    def do_quit(self, arg):
        """Clean-up and do underlying quit."""
        try:
            return self.debugger.do_quit(self, arg)
        finally:
            self.shutdown()

    do_q = do_exit = do_quit

    def do_EOF(self, arg):
        """Clean-up and do underlying EOF."""
        try:
            return self.debugger.do_EOF(self, arg)
        finally:
            self.shutdown()

    # TODO best approach here would be to bind the interactive ipy session to the new pipes we setup
    # def do_interact(self, arg):
    #     ipshell = embed.InteractiveShellEmbed(
    #         config=self.shell.config,
    #         banner1="*interactive*",
    #         exit_msg="*exiting interactive console...*",
    #     )
    #     global_ns = self.curframe.f_globals
    #     ipshell(
    #         module=sys.modules.get(global_ns["__name__"], None),
    #         local_ns=self.curframe_locals,
    #     )


def _get_debugger(addr, port):
    try:
        return get_debugger_class()(addr=addr, port=port)
    except socket.error as e:
        if OCCUPIED.is_claimed(port, sys.stdout):
            # rpdb is already on this port - good enough, let it go on:
            safe_print("recurrent rpdb invocation ignored")
            return None
        else:
            # Port occupied by something else.
            safe_print("target port is already in use. Original error: %s" % e)
            return None


def set_trace(addr=None, port=None, frame=None):
    """Wrapper function to keep the same 'import x; x.set_trace()' interface.

    We catch all the possible exceptions from pdb and cleanup.

    """

    start_time = time.time()
    timeout = 60 * 3
    retry_interval = 10

    # Keep trying until timeout
    while True:
        debugger = _get_debugger(addr, port)
        if debugger:
            break

        # Check if we've exceeded the timeout
        elapsed = time.time() - start_time
        if timeout <= 0 or elapsed >= timeout:
            safe_print(f"Giving up after {elapsed:.1f}s - port {port} is still in use")
            return

        remaining = timeout - elapsed
        retry_wait = min(retry_interval, remaining)
        safe_print(
            f"Port {port} is busy, retrying in {retry_wait:.1f}s (timeout in {remaining:.1f}s)"
        )
        time.sleep(retry_wait)

    # we can't just find another available port, since there's only one stdin & stdout

    #  we tried with a separate port, it still failed : /
    if not debugger:
        return

    try:
        debugger.set_trace(frame or sys._getframe().f_back)
    except Exception:
        traceback.print_exc()


def _trap_handler(addr, port, signum, frame):
    set_trace(addr, port, frame=frame)


def handle_trap(addr=None, port=None):
    """Register rpdb as the SIGTRAP signal handler"""
    signal.signal(signal.SIGTRAP, partial(_trap_handler, addr, port))


def post_mortem(addr=None, port=None):
    type, value, tb = sys.exc_info()
    traceback.print_exc()

    debugger = get_debugger_class()(addr=addr, port=port)
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
        got = self.claims.get(port) == id(handle)
        self.lock.release()
        return got

    def unclaim(self, port):
        self.lock.acquire(True)
        self.claims.pop(port, None)
        self.lock.release()


# {port: sys.stdout} pairs to track recursive rpdb invocation on same port.
# This scheme doesn't interfere with recursive invocations on separate ports -
# useful, eg, for concurrently debugging separate threads.
OCCUPIED = OccupiedPorts()
