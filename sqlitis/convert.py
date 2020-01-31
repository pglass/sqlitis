import logging

import sqlparse
import sqlparse.tokens as T
import sqlparse.sql as S

import sqlitis.models as M
from sqlitis.debug import debug

LOG = logging.getLogger(__name__)


def remove_whitespace(tokens):
    return [x for x in tokens if not x.is_whitespace]


@debug
def to_sqla(sql):
    sql = sql.strip()
    if not sql:
        raise Exception("Empty SQL string provided")

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

        if tok.normalized in ["INSERT", "UPDATE", "DELETE"]:
            raise Exception("'{}' is not supported yet. Sorry!".format(tok.normalized))

        if tok.normalized == "SELECT":
            m = m.Select()
        elif tok.normalized == "DISTINCT":
            m = m.Distinct()
        elif tok.normalized == "FROM":
            m = m.From()
        elif tok.normalized == "LIMIT":
            if next_tok:
                # TODO: Support `LIMIT 1 + 2`
                m = m.Limit(next_tok.normalized)
                i += 1
            else:
                raise Exception("Missing limit value")
        elif tok.normalized == "OFFSET":
            if not next_tok:
                raise Exception("Missing offset value")
            elif not isinstance(m, M.LimitOffset):
                raise Exception("Cannot use OFFSET without LIMIT")
            # TODO: Support `OFFSET 1 + 2`
            m = m.Offset(next_tok.normalized)
            i += 1
        elif tok.normalized in ["JOIN", "INNER JOIN"]:
            if next_tok:
                m = m.Join(next_tok.normalized)
                i += 1
            else:
                raise Exception("Missing argument to join")
        elif tok.normalized == "CROSS JOIN":
            if next_tok:
                m = m.CrossJoin(next_tok.normalized)
                i += 1
            else:
                raise Exception("Missing argument to join")
        elif tok.normalized in ["AND", "OR"]:
            raise Exception("misplaced operator %s" % tok.normalized)
        elif tok.normalized == "ON":
            clause, length = comparison_to_sqla(tokens[i + 1 :])
            m = m.On(clause)
            i += length
        elif type(tok) is S.Where:
            subtokens = remove_whitespace(tok.tokens[2:])
            LOG.debug("WHERE <%s tokens>", len(subtokens))
            clause, _ = comparison_to_sqla(subtokens)
            m = m.Where(clause)
        elif type(tok) is S.IdentifierList:
            if prev_tok.normalized == "FROM":
                for x in tok.get_identifiers():
                    m = m.CrossJoin(M.Table(x.normalized))
            else:
                cols = []
                for x in tok.get_identifiers():
                    cols.append(M.Field(x.normalized, alias=x.get_alias()))
                m = m.Columns(cols)
        elif type(tok) is S.Identifier:
            if prev_tok is not None and prev_tok.normalized in ["SELECT", "DISTINCT"]:
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
            elif prev_tok.normalized == "JOIN":
                sub = tokens_to_sqla(subtokens)
                m = m.Join(sub)
            # "on (foo.val > 1 or foo.thing = 'whatever') and ..."
            elif prev_tok.normalized == "ON":
                clause, _ = comparison_to_sqla(subtokens)
                m.On(clause)
            else:
                LOG.warning("not sure how to handle parentheses. treating as subquery!")
                sub = tokens_to_sqla(subtokens)
                m = m.Table(sub)
        elif tok.is_keyword:
            # Not the right error message in all cases, but better than nothing
            raise Exception(
                "Unexpected keyword '{0}'. This may be an invalid keyword, or unsupported "
                "at this time.\nTo use a keyword as a plain string, use backticks: "
                "`{0}`".format(tok.normalized)
            )

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
        "AND": 2,
        "OR": 1,
        "BETWEEN": 0,
        "NOT": -1,
    }
    fns = {
        "AND": lambda a, b: M.And(a, b),
        "OR": lambda a, b: M.Or(a, b),
        "BETWEEN": lambda a, b: M.Between(a, b),
        "NOT": lambda a: M.Not(a),
    }

    @debug
    def _shift(val, args):
        args.append(val)

    @debug
    def _reduce(args, ops):
        assert len(ops) >= 1
        op_name = ops.pop()
        op = fns[op_name]

        # handling unary operators
        if op_name in ["NOT"]:
            assert len(args) >= 1
            arg = args.pop()
            m = op(arg)
            LOG.debug("_reduce %s %s = %s", op_name, arg.render(), m.render())
        else:
            assert len(args) >= 2
            right = args.pop()
            left = args.pop()
            m = op(left, right)
            LOG.debug(
                "_reduce %s %s %s = %s",
                op_name,
                right.render(),
                left.render(),
                m.render(),
            )
        args.append(m)

    # stacks for a shift-reduce parser
    ARGS = []
    OPS = []

    for count, tok in enumerate(tokens, 1):
        if type(tok) is S.Parenthesis:
            subtokens = remove_whitespace(tok.tokens)
            m, _ = comparison_to_sqla(subtokens[1:-1])
            _shift(m, ARGS)
        # sqlparse packages up conditional AND/OR clauses as Comparisons
        elif type(tok) is S.Comparison:
            m = build_comparison(tok)
            _shift(m, ARGS)
        elif tok.normalized in precedence:
            while OPS and precedence[OPS[-1]] >= precedence[tok.normalized]:
                _reduce(ARGS, OPS)
            _shift(tok.normalized, OPS)
        # sqlparse does not package up other expressions, like Between
        elif type(tok) is S.Identifier or tok.ttype in [
            T.Literal,
            T.String,
            T.Number,
            T.Number.Integer,
            T.Number.Float,
        ]:
            m = sql_literal_to_model(tok)
            _shift(m, ARGS)
        else:
            # don't count unconsumed tokens
            count -= 1
            break

        LOG.debug("%s: OPS=%s ARGS=%s", count, OPS, ARGS)

    while OPS and len(ARGS) >= 1:
        _reduce(ARGS, OPS)

    if len(ARGS) != 1:
        raise Exception("invalid comparison clause: %s" % tokens)
    return ARGS.pop(), count


@debug
def sql_literal_to_model(tok, m=M):
    """
    :param m: the source model to "append" the literal to.
        defaults to M - the sqlitis models module (which means a fresh model
        is created)
    :return: the resulting model
    """

    def is_string_literal(tok):
        text = tok.normalized
        return all([text.startswith('"'), text.endswith('"')])

    # sqlparse treats string literals as identifiers
    if type(tok) is S.Identifier and is_string_literal(tok):
        return m.Field(tok.normalized, literal=True)
    elif type(tok) is S.Identifier:
        return m.Field(tok.normalized)
    elif tok.ttype is T.Comparison:
        return m.Op(tok.normalized)
    elif tok.ttype in [T.Literal, T.String, T.Number, T.Number.Integer, T.Number.Float]:
        return m.Field(tok.normalized, literal=True)

    return None


@debug
def build_comparison(token):
    assert type(token) is S.Comparison

    m = M.Comparison()
    for tok in remove_whitespace(token.tokens):
        LOG.debug("  %s %s", tok, type(tok))
        if type(tok) is S.Parenthesis:
            subtokens = remove_whitespace(tok.tokens)
            subquery = tokens_to_sqla(subtokens[1:-1])
            if not m.left:
                m.left = subquery
            else:
                m.right = subquery
        else:
            m = sql_literal_to_model(tok, m)
            if not m:
                raise Exception("[BUG] Failed to convert %s to model" % tok)

    return m
