rpdb - remote debugger based on pdb
==================================

This is essentially a wrapper around pdb that will re-route stdin and stdout to
a socket handler. By default it opens the debugger on port 4444::

    import rpdb; rpdb.set_trace()

But you can change that by simply instantiating Rpdb manually::

    import rpdb
    debugger = rpdb.Rpdb(12345)
    debugger.set_trace()

It is known to work on Jython 2.5, Python 2.5 and Python 3.1. It was written
originally for Jython since this is pretty much the only way to debug it when
running it on Tomcat.

After that your script will "hang" when entering set_trace() and the only
way to get it to continue is to access rpdb using telnet, netcat, etc..::

    nc 127.0.0.1 4444

Installation on CPython (standard Python)
-----------------------------------------

    python setup.py install

Installation in a Tomcat webapp
-------------------------------

Just copy the rpdb directory (the one with the __init__.py file) in your
WEB-INF/lib/Lib folder along with the standard Jython library (required).

Known bugs
----------
  - The socket is now closed properly so you will need to ^C in netcat and ^\
    in telnet to exit after a continue.
  - For some obscure reason, you will need to run continue twice on Jython.

Author(s)
---------
Bertrand Janin <tamentis@neopulsar.org> - http://tamentis.com/

The idea comes from there:

    http://bugs.python.org/issue721464
    http://snippets.dzone.com/posts/show/7248
