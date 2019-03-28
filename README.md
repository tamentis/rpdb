# rpdb - remote debugger based on pdb

rpdb is a wrapper around pdb that re-routes stdin and stdout to a socket
handler. 

It has two modes: passive and active:

## Passive mode

By default it opens the debugger on port 4444::

    import rpdb; rpdb.set_trace()

But you can change that by simply instantiating Rpdb manually::

    import rpdb
    debugger = rpdb.Rpdb(port=12345)
    debugger.set_trace()

It is known to work on Jython 2.5 to 2.7, Python 2.5 to 3.1. It was written
originally for Jython since this is pretty much the only way to debug it when
running it on Tomcat.

Upon reaching `set_trace()`, your script will "hang" and the only way to get it
to continue is to access rpdb using telnet, netcat, etc..::

    nc 127.0.0.1 4444

## Active mode

You can add `active=True` flag to `set_trace`, and then *rpdb* will connect to
your terminal. It's useful when you want to debug app which can break
simultaneously more than once in a time, and passive mode will refuse to open
port 4444 again.

Solution to the problem is:

    # default host is 127.0.0.1 and default port is 4444
    import rpdb; rpdb.set_trace(active=True)

or, in more complex case, eg. when it's running in other host, in your docker, or sth like that

    import rpdb
    rpdb.set_trace(addr='192.168.1.120', port=12345)

You should have arpdb-cli running on other side of your communication. 

### arpdb-cli

arpdb-cli is a simple tool, using tmux, tcpwrapper and socat to accept incoming
connections and spawn tmux session for each incoming breakpoint. 


Installation in CPython (standard Python)
-----------------------------------------

    pip install rpdb

For a quick, ad hoc alternative, you can copy the entire rpdb subdirectory
(the directory directly containing the __init__.py file) to somewhere on your
$PYTHONPATH.

Installation in a Tomcat webapp
-------------------------------

Just copy the rpdb directory (the one with the __init__.py file) in your
WEB-INF/lib/Lib folder along with the standard Jython library (required).

Trigger rpdb with signal
------------------------

`set_trace()` can be triggered at any time by using the TRAP signal handler.
This allows you to debug a running process independantly of a specific failure
or breakpoint::

    import rpdb
    rpdb.handle_trap()

    # As with set_trace, you can optionally specify addr and port
    rpdb.handle_trap("0.0.0.0", 54321)

Calling `handle_trap` will overwrite the existing handler for SIGTRAP if one has
already been defined in your application.

Known bugs
----------
  - The socket is not always closed properly so you will need to ^C in netcat
    and Esc+q in telnet to exit after a continue or quit.
  - There is a bug in Jython 2.5/pdb that causes rpdb to stop on ghost
    breakpoints after you continue ('c'), this is fixed in 2.7b1.

Author(s)
---------
Bertrand Janin <b@janin.com> - http://tamentis.com/

With contributions from (chronological, latest first):

 - Cameron Davidson-Pilon - @CamDavidsonPilon
 - Pavel Fux - @fuxpavel
 - Ken Manheimer - @kenmanheimer
 - Steven Willis - @onlynone
 - Jorge Niedbalski R <niedbalski@gmail.com>
 - Cyprien Le Pannérer <clepannerer@edd.fr>
 - k4ml <kamal.mustafa@gmail.com>
 - Sean M. Collins <sean@coreitpro.com>
 - Sean Myers <sean.myers@redhat.com>

This is inspired by:

 - http://bugs.python.org/issue721464
 - http://snippets.dzone.com/posts/show/7248
