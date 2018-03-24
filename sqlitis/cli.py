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
    parser.add_argument('sql', nargs='*')
    parser.add_argument('--web', action='store_true')

    return parser.parse_args()


def web(debug=False):
    try:
        from web.app import app
    except ImportError as e:
        print("Cannot start web server: %s" % e, file=sys.stderr)
        return 1

    app.run(debug=debug, port=7070)


def main():
    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.web:
        return web(debug=args.debug)

    sql = (" ".join(args.sql) if args.sql else '').strip()
    if not sql:
        print(
            "No sql provided. Try `%s 'select * from bar'`" % sys.argv[0],
            file=sys.stderr
        )
        return 1

    try:
        result = to_sqla(sql)
        print(result)
    except Exception as e:
        print(e, file=sys.stderr)
        if args.debug:
            raise
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
