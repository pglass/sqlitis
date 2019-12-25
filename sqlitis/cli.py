from __future__ import print_function
import argparse
import logging
import sys

from sqlitis.convert import to_sqla
from sqlitis.debug import version_info
from sqlitis.version import VERSION

LOG = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert sql to sqlalchemy expressions"
    )

    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-V", "--version", action="store_true")
    parser.add_argument("sql", nargs="*", default=None)

    return parser.parse_args()


def main():
    args = parse_args()
    if args.version:
        print("sqlitis %s" % VERSION)
        return 0

    if not args.sql:
        print("ERROR: No SQL string provided", file=sys.stderr)
        return 1

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # log version info
    LOG.debug("Version info")
    for key, val in version_info().items():
        LOG.debug("  %s: %s", key, val)

    sql_string = " ".join(args.sql)
    try:
        result = to_sqla(sql_string)
        print(result)
    except Exception as e:
        print("ERROR: Failed to convert SQL: {}".format(sql_string), file=sys.stderr)
        print("{}".format(e), file=sys.stderr)
        if args.debug:
            raise
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
