# pylint: disable=invalid-name
"""
example of using active rpdb in multithreading environment
"""
import threading

import rpdb


def worker():
    """thread worker function"""
    print('Worker')
    rpdb.set_trace(active=True, port=9876)
    print("After")


def main():
    """just main"""
    threads = []
    for _ in range(5):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()


if __name__ == '__main__':
    main()
