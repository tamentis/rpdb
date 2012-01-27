"""Remote Python Debugger (pdb wrapper)."""

__author__ = "Bertrand Janin <tamentis@neopulsar.org>"
__version__ = "0.1.2"

import pdb
import socket
import sys


class Rpdb(pdb.Pdb):

    def __init__(self, port=4444):
        """Initialize the socket and initialize pdb."""
        addr = socket.gethostname()

        # Writes to stdout are forbidden in mod_wsgi environments
        try:
            print("pdb is running on %s:%d" % (addr, port))
        except IOError:
            pass

        # Backup stdin and stdout before replacing them by the socket handle
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin

        # Open a 'reusable' socket to let the webapp reload on the same port
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.skt.bind((addr, port))
        self.skt.listen(1)
        (clientsocket, address) = self.skt.accept()
        handle = clientsocket.makefile('rw')
        pdb.Pdb.__init__(self, completekey='tab', stdin=handle, stdout=handle)
        sys.stdout = sys.stdin = handle

    def shutdown(self):
        """Revert stdin and stdout, close the socket."""
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        self.skt.close()
        self.set_continue()

    def do_continue(self, arg):
        """Stop all operation on ``continue``."""
        self.shutdown()
        return 1

    do_EOF = do_quit = do_exit = do_c = do_cont = do_continue


def set_trace():
    """Wrapper function to keep the same import x; x.set_trace() interface.

    We catch all the possible exceptions from pdb and cleanup.

    """
    debugger = Rpdb()
    try:
        debugger.set_trace(sys._getframe().f_back)
    finally:
        debugger.shutdown()

