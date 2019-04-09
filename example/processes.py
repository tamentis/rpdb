import concurrent.futures as cf
import click
import time

SLEEPTIME = 5


def fib(num):
    import rpdb
    rpdb.set_trace(active=True)
    assert num >= 0
    if num == 0:
        return 0
    if num == 1:
        return 1

    time.sleep(SLEEPTIME)

    with cf.ProcessPoolExecutor() as ex:
        a = ex.submit(fib, num - 1)
        b = ex.submit(fib, num - 2)
        return a.result() + b.result()


@click.command()
@click.option("--number", "-n", type=int, required=True)
@click.option("--sleeptime", "-t", type=int, help="how long wait on function time", default=SLEEPTIME)
def main(number, sleeptime):
    global SLEEPTIME
    SLEEPTIME = sleeptime
    print("fib(%s) = %s" % (number, fib(number)))


if __name__ == '__main__':
    main()
