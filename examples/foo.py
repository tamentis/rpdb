#!/usr/bin/env python

from __future__ import print_function

import logging
import rpdb

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    lh = logging.StreamHandler()
    logger.addHandler(lh)

def main():
    count = 0
    while count < 10:
        rpdb.set_trace()
        print("here %d" % count)
        count += 1

    print("done")

try:
    main()
except Exception as e:
    logger.exception(e)
    rpdb.post_mortem()
