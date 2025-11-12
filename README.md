# rpdb - remote debugger based on pdb

rpdb is a wrapper around pdb that re-routes stdin and stdout to a socket
handler. By default it opens the debugger on port 4444:

```python
import rpdb; rpdb.set_trace()
```

But you can change that by simply instantiating Rpdb manually:

```python
import rpdb
debugger = rpdb.Rpdb(port=12345)
debugger.set_trace()
```

It is known to work on Jython 2.5 to 2.7, Python 2.5 to 3.1. It was written
originally for Jython since this is pretty much the only way to debug it when
running it on Tomcat.

Upon reaching `set_trace()`, your script will "hang" and the only way to get it
to continue is to access rpdb using telnet, netcat, etc..:

```shell
nc 127.0.0.1 4444
```

Or, even better, you can use socat to enable some additional readline-related features (tab completion still doesn't work, though):

```shell
socat TCP:0.0.0.0:444 READLINE
```

## Configuration

### Environment Variables

You can configure rpdb without changing your code by setting these environment variables:

- `PYTHON_RPDB_ADDRESS` - Override the default bind address (default: "127.0.0.1")
- `PYTHON_RPDB_PORT` - Override the default port (default: 4444)
- `PYTHON_RPDB_FIND_AVAILABLE_PORT` - Enable automatic port selection if the port is busy (default: "1")

```shell
export PYTHON_RPDB_PORT=5555
export PYTHON_RPDB_ADDRESS="0.0.0.0"
python your_script.py
```

### Dynamic Port Selection

When you have multiple debugging sessions or forked processes, rpdb will automatically find the next available port if your configured port is in use. This is particularly helpful when debugging concurrent applications.

If port 4444 is busy, rpdb will scan up to 100 ports and bind to the first available one. You'll see a message like:

```
[rpdb] port 4444 is in use, using 4445 instead
```

To disable this behavior, set `PYTHON_RPDB_FIND_AVAILABLE_PORT=0`.

### Use Cases

* breakpoints in a fastapi development server. Stdin gets corrupted because of the subprocess setup such that interactive debuggers don't work.
* systems which consume stdin (such as [Estuary connector](https://estuary.dev) which consumes jsonlines over stdin)

## Installation in CPython (standard Python)

```shell
pip install rpdb
```

For a quick, ad hoc alternative, you can copy the entire rpdb subdirectory
(the directory directly containing the __init__.py file) to somewhere on your
`$PYTHONPATH`.

## Installation in a Tomcat webapp

Just copy the rpdb directory (the one with the __init__.py file) in your
WEB-INF/lib/Lib folder along with the standard Jython library (required).

## Trigger rpdb with signal

`set_trace()` can be triggered at any time by using the TRAP signal handler.
This allows you to debug a running process independently of a specific failure
or breakpoint:

```python
import rpdb
rpdb.handle_trap()

# As with set_trace, you can optionally specify addr and port
rpdb.handle_trap("0.0.0.0", 54321)
```

Calling `handle_trap` will overwrite the existing handler for SIGTRAP if one has
already been defined in your application.

## Advanced Features

### Post-mortem Debugging

When you hit an exception, you can start rpdb in post-mortem mode to inspect the state at the time of the crash:

```python
import rpdb

try:
    # your code that might fail
    problematic_function()
except Exception:
    rpdb.post_mortem()
```

### Automatic Debugging on Exceptions

Use the context manager to automatically drop into rpdb when any exception occurs:

```python
from rpdb import launch_ipdb_on_exception

with launch_ipdb_on_exception():
    # any exception in this block will trigger rpdb
    your_code_here()

# or use the shorter alias
from rpdb import iex

with iex:
    your_code_here()
```

### IPython Integration

If you have IPython installed, rpdb automatically uses IPython's debugger for better introspection, syntax highlighting, and tab completion. No configuration needed - just `pip install ipython` and rpdb will detect it.

### Connection Retry Logic

When `set_trace()` is called and the port is busy, rpdb will retry for up to 3 minutes with 10-second intervals. This is useful in scenarios where you have multiple breakpoints or concurrent processes. You'll see progress messages during the wait.

## Known bugs

- The socket is not always closed properly so you will need to ^C in netcat
  and Esc+q in telnet to exit after a continue or quit.
- There is a bug in Jython 2.5/pdb that causes rpdb to stop on ghost
  breakpoints after you continue ('c'), this is fixed in 2.7b1.

## Author(s)

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
