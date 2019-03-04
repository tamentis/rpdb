# pylint: disable=invalid-name
"""
example of using active rpdb in multithreading environment
"""
from random import random, randint
import threading
import time

import rpdb


def worker():
    """thread worker function"""
    rpdb.set_trace(active=True, port=9876)
    num = randint(1, 100)
    for x in range(num):
        print(x)
        time.sleep(x + random())


def main():
    """just main"""
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()


if __name__ == '__main__':
    main()
