import asyncio
from itertools import cycle

from aioconsole import ainput
import click


# I assume that there will be no more than ~20 connected sessions concurrently
CHARS_ITER = cycle('ABCDEFGHJKLMNOPRSTUWVXYZ')
writers = []


def writer_desc(writer):
    try:
        desc = writer._writer_desc
    except AttributeError:
        _ign, port = writer.get_extra_info('peername')
        writer._writer_desc = desc = "{}:{}".format(next(CHARS_ITER), port)

    return desc


async def process_server(reader, addr):
    global writers
    while True:
        data = await reader.readline()
        message = data.decode()

        print("{addr}: {msg}".format(addr=addr, msg=message), end='', flush=True)


async def process_stdin():
    global writers
    while True:
        data = await ainput("$ ")
        if not writers:
            print("NO SESSION CONNECTED YET")
            continue

        if data == "/switch":
            writers = writers[1:] + writers[:1]
            print("(switched to %s)" % writer_desc(writers[0]))
            continue

        writer = writers[0]

        writer.write(data.encode("utf8")+b"\n")


async def handle_session(reader, writer):
    global writers
    writers.append(writer)
    desc = writer_desc(writer)

    print("(Session %s connected)" % desc)

    task_server = asyncio.create_task(process_server(reader, desc))

    await task_server

    print("Close the connection")
    writer.close()
    reader.close()


async def main(port):
    server = await asyncio.start_server(handle_session, '127.0.0.1', port)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    task_stdin = asyncio.create_task(process_stdin())
    async with server:
        await server.serve_forever()
        await task_stdin


@click.command()
@click.option("--port", "-p")
def smain(port):
    asyncio.run(main(port))
