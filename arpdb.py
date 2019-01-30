import pdb
import sys
import socket

from .rpdb import Rpdb, FileObjectWrapper


class ARprb(Rpdb):
    """ active version of RPDB. Instead of listning for connection, it actively
    tries to make one

    TODO: continue run when unable to connect to mentioned host/port"""

    def __init__(self, addr, port):
        # backup
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.addr = self.addr
        self.port = self.port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.conect((self.addr, self.port))

        try:
            sys.stderr.write("rpdb tries to connect to %s:%s" % (self.addr, self.port))
        except IOError:
            pass

        handle = self.sock.makefile("rw")

        pdb.Pdb.__init__(self, completekey='tab',
                         stdin=FileObjectWrapper(handle, self.old_stdin),
                         stdout=FileObjectWrapper(handle, self.old_stdin))
        sys.stdout = sys.stdin = handle
