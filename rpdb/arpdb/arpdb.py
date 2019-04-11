import pdb
import sys
import socket

from ..rpdb import Rpdb, FileObjectWrapper


class ARpdb(Rpdb):
    """ active version of RPDB. Instead of listning for connection, it actively
    tries to make one

    TODO: continue run when unable to connect to mentioned host/port"""

    def __init__(self, addr, port):
        # backup
        self.old_stdout, self.old_stdin = sys.stdout, sys.stdin
        self.addr, self.port = addr, port

        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.connect((self.addr, self.port))

        try:
            sys.stderr.write("rpdb tries to connect to %s:%s\n\n" % (self.addr, self.port))
        except IOError:
            pass

        self.handle = self.skt.makefile("rw")

        pdb.Pdb.__init__(self, completekey='tab',
                         stdin=FileObjectWrapper(self.handle, self.old_stdin),
                         stdout=FileObjectWrapper(self.handle, self.old_stdin))
        sys.stdout = sys.stdin = self.handle
