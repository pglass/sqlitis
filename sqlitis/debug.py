import logging
import platform

import sqlparse.sql as S

from sqlitis.version import VERSION

LOG = logging.getLogger(__name__)


def version_info():
    return {
        "sqlitis": VERSION,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def debug_tokens(tokens):
    for t in tokens:
        LOG.debug("  %r %s", t, type(t))


def is_tokens(x):
    return isinstance(x, list) and len(x) > 0 and isinstance(x[0], S.Token)


def debug(f):
    """Decorator for functions. Provies useful debug logging"""

    def wrapped(*args, **kwargs):
        debug_args = []
        for a in args:
            if is_tokens(a):
                debug_args.append("[<%s tokens>]" % len(a))
            else:
                debug_args.append("%r" % a)

        args_str = " ".join(str(a) for a in debug_args)
        kwargs_str = " ".join("%s=%s" for k, v in kwargs.items())
        LOG.debug("%s %s", f.__name__, args_str + kwargs_str)

        # try to find tokens
        if "tokens" in kwargs:
            if is_tokens(kwargs["tokens"]):
                debug_tokens(kwargs["tokens"])
        for a in args:
            if is_tokens(a):
                debug_tokens(a)

        result = f(*args, **kwargs)
        if result is not None:
            LOG.debug("%s returned %r", f.__name__, result)
        return result

    return wrapped
