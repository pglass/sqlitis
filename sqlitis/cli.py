from __future__ import print_function
import argparse
import logging
import sys

from sqlitis.convert import to_sqla


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert sql to sqlalchemy expressions"
    )

    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('sql', nargs='+')

    return parser.parse_args()


def main():
    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        result = to_sqla(" ".join(args.sql))
        print(result)
    except Exception as e:
        print(e, file=sys.stderr)
        if args.debug:
            raise
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
