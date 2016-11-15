#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from .utils import PY3K
from .bridge import Bridge
from .exception import PhueRegistrationException


def main():
    import argparse

    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--config-file-path', required=False)
    args = parser.parse_args()

    while True:
        try:
            Bridge(args.host, config_file_path=args.config_file_path)
            break
        except PhueRegistrationException as e:
            if PY3K:
                input('Press button on Bridge then hit Enter to try again')
            else:
                raw_input('Press button on Bridge then hit Enter to try again')  # noqa

if __name__ == '__main__':
    main()
