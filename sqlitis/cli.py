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
        print to_sqla(" ".join(args.sql))
    except Exception as e:
        print >> sys.stderr, e
        if args.debug:
            raise

    sys.exit(0)


if __name__ == '__main__':
    main()
