import sqlparse
import sqlparse.tokens as T
import sqlparse.sql as S

import models as M

import logging
LOG = logging.getLogger(__name__)


def debug_tokens(tokens):
    for t in tokens:
        LOG.debug('  %r %s', t, type(t))


def is_tokens(x):
    return isinstance(x, list) and len(x) > 0 and isinstance(x[0], S.Token)


def debug(f):

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
        if 'tokens' in kwargs:
            if is_tokens(kwargs['tokens']):
                debug_tokens(kwargs['tokens'])
        for a in args:
            if is_tokens(a):
                debug_tokens(a)

        result = f(*args, **kwargs)
        LOG.debug("%s returned %r", f.__name__, result)
        return result

    return wrapped


def remove_whitespace(tokens):
    return [x for x in tokens if not x.is_whitespace()]


@debug
def to_sqla(sql):
    tokens = sqlparse.parse(sql)[0].tokens
    tokens = remove_whitespace(tokens)
    return tokens_to_sqla(tokens)


@debug
def tokens_to_sqla(tokens):
    if not tokens:
        return None

    i = 0
    m = M
    while i < len(tokens):
        prev_tok = None if i - 1 < 0 else tokens[i - 1]
        tok = tokens[i]
        next_tok = None if i + 1 >= len(tokens) else tokens[i + 1]

        if tok.normalized == 'SELECT':
            m = m.Select()
        elif tok.normalized == 'FROM':
            m = m.From()
        elif tok.normalized == 'JOIN':
            if next_tok:
                m = m.Join(next_tok.normalized)
                i += 1
            else:
                raise Exception("Missing argument to join")
        elif tok.normalized in ['AND', 'OR']:
            raise Exception("misplaced operator %s" % tok.normalized)
        elif tok.normalized == 'ON':
            clause, length = comparison_to_sqla(tokens[i + 1:])
            m = m.On(clause)
            i += length
        elif tok.normalized == '*':
            m = m.Star()
        elif type(tok) is S.IdentifierList:
            m = m.Columns([x.normalized for x in tok.get_identifiers()])
        elif type(tok) is S.Identifier:
            if prev_tok is not None and prev_tok.normalized == 'SELECT':
                m = m.Columns([tok.normalized])
            else:
                m = m.Table(tok.normalized)
        elif type(tok) is S.Comparison:
            raise Exception("misplaced comparison %s" % tok)
        elif type(tok) is S.Parenthesis:
            subtokens = remove_whitespace(tok.tokens[1:-1])
            # whole expression has parens - "(select * from thing)"
            if prev_tok is None:
                sub = tokens_to_sqla(subtokens)
                m = sub
            # "join (select id, name from ...)"
            elif prev_tok.normalized == 'JOIN':
                sub = tokens_to_sqla(subtokens)
                m = m.Join(sub)
            # "on (foo.val > 1 or foo.thing = 'whatever') and ..."
            elif prev_tok.normalized == 'ON':
                clause, _ = comparison_to_sqla(subtokens)
                m.On(clause)
            else:
                LOG.warning(
                    "not sure how to handle parentheses - trying something!"
                )
                sub = tokens_to_sqla(subtokens)
                m = m.Table(sub)

        LOG.debug("%s %s", i, type(m))
        i += 1

    if isinstance(m, M.Base):
        return m.render()
    return None


@debug
def comparison_to_sqla(tokens):

    # the comparison expression can start with
    #   "(x > 1 or y < 2)"
    #   "x > 1 and y > 2"
    if type(tokens[0]) is S.Parenthesis:
        subtokens = remove_whitespace(tokens[0].tokens[1:-1])
        m, _ = comparison_to_sqla(subtokens)
    elif type(tokens[0]) is S.Comparison:
        m = build_comparison(tokens[0])
    else:
        raise Exception("bad call to comparison_to_sqla")

    count = 1
    for tok in tokens[1:]:
        if tok.normalized == 'AND':
            m = m.And()
        elif tok.normalized == 'OR':
            m = m.Or()
        elif type(tok) is S.Parenthesis:
            subtokens = remove_whitespace(tok.tokens)
            assert isinstance(m, M.Conjuction)
            m.right, _ = comparison_to_sqla(subtokens[1:-1])
        elif type(tok) is S.Comparison:
            assert isinstance(m, M.Conjuction)
            m.right = build_comparison(tok)
        else:
            break

        count += 1

        LOG.debug(" %r", tok)

    return m, count


@debug
def build_comparison(tok):
    assert type(tok) is S.Comparison

    m = M.Comparison()
    for tok in remove_whitespace(tok.tokens):
        if type(tok) is S.Identifier:
            m = m.Field(tok.normalized)
        elif tok.ttype is T.Comparison:
            m = m.Op(tok.normalized)
        elif tok.ttype in [
            T.Literal, T.String, T.Number, T.Number.Integer, T.Number.Float
        ]:
            m = m.Field(tok.normalized, literal=True)

    return m
