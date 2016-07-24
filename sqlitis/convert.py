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
        if result is not None:
            LOG.debug("%s returned %r", f.__name__, result)
        return result

    return wrapped


def remove_whitespace(tokens):
    return [x for x in tokens if not x.is_whitespace()]


@debug
def to_sqla(sql):
    tokens = sqlparse.parse(sql)[0].tokens
    tokens = remove_whitespace(tokens)
    return tokens_to_sqla(tokens).render()


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
        elif type(tok) is S.Where:
            subtokens = remove_whitespace(tok.tokens[2:])
            LOG.debug('WHERE <%s tokens>', len(subtokens))
            clause, _ = comparison_to_sqla(subtokens)
            m = m.Where(clause)
        elif type(tok) is S.IdentifierList:
            cols = []
            for x in tok.get_identifiers():
                cols.append(M.Field(x.normalized, alias=x.get_alias()))
            m = m.Columns(cols)
        elif type(tok) is S.Identifier:
            if prev_tok is not None and prev_tok.normalized == 'SELECT':
                m = m.Columns([M.Field(tok.normalized, alias=tok.get_alias())])
            else:
                m = m.Table(tok.normalized)
        elif type(tok) is S.Comparison:
            raise Exception("misplaced comparison %s" % tok)
        elif type(tok) is S.Parenthesis:
            subtokens = remove_whitespace(tok.tokens[1:-1])
            # whole expression has parens - "(select * from thing)"
            if prev_tok is None:
                m = tokens_to_sqla(subtokens)
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
                    "not sure how to handle parentheses. treating as subquery!"
                )
                sub = tokens_to_sqla(subtokens)
                m = m.Table(sub)

        LOG.debug("%s %s", i, type(m))
        i += 1

    if isinstance(m, M.Base):
        return m
    return None


@debug
def comparison_to_sqla(tokens):
    # operators of higher precedence "steal" arguments first.
    # 'x OR y AND z OR w' is equivalent to 'x OR (y AND z) OR w'.
    precedence = {
        'AND': 2,
        'OR': 1,
    }
    fns = {
        'AND': lambda a, b: M.And(a, b),
        'OR': lambda a, b: M.Or(a, b),
    }

    @debug
    def _shift(val, args):
        args.append(val)

    @debug
    def _reduce(args, ops):
        assert len(args) >= 2
        assert len(ops) >= 1
        right = args.pop()
        left = args.pop()
        op = fns[ops.pop()]
        m = op(left, right)
        args.append(m)

    # stacks for a shift-reduce parser
    ARGS = []
    OPS = []

    for count, tok in enumerate(tokens, 1):
        if type(tok) is S.Parenthesis:
            subtokens = remove_whitespace(tok.tokens)
            m, _ = comparison_to_sqla(subtokens[1:-1])
            _shift(m, ARGS)
        elif type(tok) is S.Comparison:
            m = build_comparison(tok)
            _shift(m, ARGS)
        elif tok.normalized in precedence:
            while OPS and precedence[OPS[-1]] >= precedence[tok.normalized]:
                if len(ARGS) < 2:
                    raise Exception("unexpected token %s" % tok)
                _reduce(ARGS, OPS)
            _shift(tok.normalized, OPS)
        else:
            break

        LOG.debug("%s: OPS=%s ARGS=%s", count, OPS, ARGS)

    while OPS and len(ARGS) > 1:
        _reduce(ARGS, OPS)

    if len(ARGS) != 1:
        raise Exception("invalid comparison clause: %s" % tokens)
    return ARGS.pop(), count


@debug
def build_comparison(tok):
    assert type(tok) is S.Comparison

    def is_string_literal(tok):
        text = tok.normalized
        return all([text.startswith('"'), text.endswith('"')])

    m = M.Comparison()
    for tok in remove_whitespace(tok.tokens):
        LOG.debug("  %s %s", tok, type(tok))
        # sqlparse mistreats string literals as identifiers
        if type(tok) is S.Identifier and is_string_literal(tok):
            m = m.Field(tok.normalized, literal=True)
        elif type(tok) is S.Identifier:
            m = m.Field(tok.normalized)
        elif tok.ttype is T.Comparison:
            m = m.Op(tok.normalized)
        elif tok.ttype in [
            T.Literal, T.String, T.Number, T.Number.Integer, T.Number.Float
        ]:
            m = m.Field(tok.normalized, literal=True)

    return m
