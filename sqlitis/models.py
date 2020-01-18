class Base(object):
    def render(self):
        return ""


def convert_column(col, table=None, quote_open="`", quote_close="`"):
    """Turns foo.id into foo.c.id. If a table is given, then id becomes
    <table>.c.id"""
    col = col.replace(quote_open, "").replace(quote_close, "")
    if "." in col and table and not col.startswith(table.name):
        raise Exception("field %s invalid for table %s" % (col, table.name))
    elif "." in col:
        if col.count(".") > 1:
            raise Exception("field '%s' invalid (too many '.')" % col)
        return ".c.".join(col.split("."))
    elif "." not in col and table:
        return "%s.c.%s" % (table.name, col)
    else:
        return "text('%s')" % col


def unquote_quoted_table_name(name, quote_open="`", quote_close="`"):
    return name.lstrip(quote_open).rstrip(quote_close)


class Select(Base):
    """
        sql                 model
        ---                 ---
        select *            Select().Star()
        select id, name     Select().Columns(['id', 'name'])
        select distinct *   Select().Distinct().Star()
    """

    def __init__(self):
        self._is_distinct = False
        self._cols = None

    def Star(self):
        return self.Columns("*")

    def Columns(self, cols):
        cols = list(cols)
        for i in range(len(cols)):
            if not isinstance(cols[i], Base):
                cols[i] = Field(cols[i])

        self._cols = cols
        return self

    def is_wildcard(self):
        return self._cols and len(self._cols) == 1 and self._cols[0].name == "*"

    def From(self):
        return SelectFrom(self)

    def Distinct(self):
        self._is_distinct = True
        return self

    def render(self):
        if self.is_wildcard():
            raise Exception("cannot render 'select *' without table")

        if not self._cols:
            result = "select()"
        else:
            result = "select([%s])" % ", ".join(c.render() for c in self._cols)

        if self._is_distinct:
            result += ".distinct()"
        return result


class SelectFrom(Base):
    """
        select * from table
        Select().star().From().Table('table')
    """

    def __init__(self, select):
        self.select = select
        self.table = None

    def Table(self, table):
        if not isinstance(table, Base):
            table = Table(table)
        self.table = table
        return self

    def Join(self, table):
        self.table = self.table.Join(table)
        return self

    def CrossJoin(self, table):
        if not self.table:
            self.table = table
        else:
            self.table = self.table.CrossJoin(table)
        return self

    def On(self, clause):
        self.table = self.table.On(clause)
        return self

    def Where(self, clause):
        return SelectFromWhere(self, clause)

    def Limit(self, value):
        return LimitOffset(self, limit=value)

    def render(self):
        if self.select.is_wildcard() or not self.select._cols:
            result = "select([%s])" % self.table.render()
        elif isinstance(self.table, Table):
            cols = [c.render(self.table) for c in self.select._cols]
            result = "select([%s])" % ", ".join(cols)
        elif isinstance(self.table, CrossJoin):
            # sqlitis can do these,
            #   select * from foo                       -> select([foo])
            #   select * from foo, bar                  -> select([foo, bar])
            #   select * from foo, bar                  -> select([foo, bar])
            #   select foo.id, bar.id from foo, bar     -> select([foo.c.id, bar.c.id])
            #
            # This one I don't know haw to represent in sqlalchemy.
            #   select foo.id from foo, bar             -> ???
            # It's a cross join, not an inner join like sqlalchemy `join()`.
            # So this is not the same, because it's an inner join.
            #     select([foo.c.id]).select_from(foo.join(bar))
            if self.select._cols:
                cols = [c.render() for c in self.select._cols]
                result = "select([%s])" % ", ".join(cols)
            else:
                result = "select([%s])" % self.table.render()
        elif isinstance(self.table, (Join, SelectFrom)):
            cols = [c.render() for c in self.select._cols]
            result = "select([%s]).select_from(%s)" % (
                ", ".join(cols),
                self.table.render(),
            )
        else:
            raise Exception("%s failed to render" % self.__class__.__name__)

        if self.select._is_distinct:
            result += ".distinct()"
        return result


class SelectFromWhere(Base):
    def __init__(self, select, clause):
        self.select = select
        self.clause = clause

    def Limit(self, value):
        return LimitOffset(self, limit=value)

    def render(self):
        return "%s.where(%s)" % (self.select.render(), self.clause.render())


class Table(Base):
    def __init__(self, name):
        self.name = unquote_quoted_table_name(name)

    def Join(self, table):
        return Join(self, table)

    def CrossJoin(self, table):
        return CrossJoin(self, table)

    def render(self):
        return self.name


class Field(Base):
    def __init__(self, name, literal=False, alias=None):
        self.name = name
        self.literal = literal
        self.alias = alias

    def render(self, table=None):
        if self.literal:
            return self.name
        result = convert_column(self.name, table)
        if self.alias:
            result = "%s.label('%s')" % (result, self.alias)
        return result


class Op(Base):
    def __init__(self, op):
        self.op = op

    def render(self):
        return {
            "=": "==",
            "<>": "!=",
            "!=": "!=",
            ">": ">",
            "<": "<",
            ">=": ">=",
            "<=": "<=",
        }[self.op]


class Join(Base):
    """
        sql:    foo join bar on foo.id = bar.foo_id
        code:   Table('foo').Join('bar').
                On().Field('foo.id').Op('=').Field('bar.foo_id')

        sql:    foo join bar on foo.id = bar.foo_id
                and foo.val <> bar.val
        code:   Table('foo').Join('bar').
                On().Field('foo.id').Op('=').Field('bar.foo_id')
                And().Field('foo.val).Op('<>').Field('bar.val')
    """

    class Item(object):
        def __init__(self, table, clause=None):
            self.table = table
            self.clause = clause

    def __init__(self, *tables):
        self._tables = []
        for t in tables:
            self.Join(t)

    def Join(self, table):
        if not isinstance(table, Base):
            table = Table(table)
        self._tables.append(Join.Item(table))
        return self

    def On(self, clause=None):
        self._tables[-1].clause = clause or Comparison()
        return self

    def And(self):
        self._tables[-1].clause = And(self._tables[-1].clause)
        return self

    def Or(self):
        self._tables[-1].clause = Or(self._tables[-1].clause)
        return self

    def Field(self, name, literal=False, alias=None):
        self._tables[-1].clause.Field(name, literal, alias)
        return self

    def Op(self, op):
        self._tables[-1].clause.Op(op)
        return self

    def render(self):
        if not self._tables:
            raise Exception("Join has no tables to join")
        result = self._tables[0].table.render()
        assert self._tables[0].clause is None
        for t in self._tables[1:]:
            if t.clause:
                result += ".join(%s, %s)" % (t.table.render(), t.clause.render())
            else:
                result += ".join(%s)" % t.table.render()
        return result


class CrossJoin(Join):
    def CrossJoin(self, table):
        return self.Join(table)

    def render(self):
        if not self._tables:
            raise Exception("CrossJoin has no tables to join")
        return ", ".join(t.table.render() for t in self._tables)


class Comparison(Base):
    def __init__(self):
        self.left = None
        self.op = None
        self.right = None

    def Field(self, name, literal=False, alias=None):
        if not self.left:
            self.left = Field(name, literal, alias)
        elif not self.right:
            self.right = Field(name, literal, alias)
        else:
            raise Exception("too many fields for comparison")
        return self

    def Op(self, op):
        self.op = Op(op)
        return self

    def And(self):
        return And(self)

    def Or(self):
        return Or(self)

    def render(self):
        return "%s %s %s" % (self.left.render(), self.op.render(), self.right.render())


class Conjuction(Base):
    def __init__(self, left, right=None):
        self.left = left
        self.right = right or Comparison()

    def Field(self, name, literal=False, alias=None):
        self.right = self.right.Field(name, literal, alias)
        return self

    def Op(self, op):
        self.right = self.right.Op(op)
        return self

    def And(self):
        return And(self)

    def Or(self):
        return Or(self)


class On(Conjuction):
    def render(self):
        return "%s" % self.right.render()


class And(Conjuction):
    def render(self):
        return "and_(%s, %s)" % (self.left.render(), self.right.render())


class Or(Conjuction):
    def render(self):
        return "or_(%s, %s)" % (self.left.render(), self.right.render())


class Not(Base):
    def __init__(self, clause):
        self.clause = clause

    def render(self):
        return "not_(%s)" % self.clause.render()


class Between(Conjuction):
    def render(self):
        if not isinstance(self.right, And):
            raise Exception("Unsupported 'Between' Clause")
        lower = self.right.left
        upper = self.right.right
        return "between(%s, %s, %s)" % (
            self.left.render(),
            lower.render(),
            upper.render(),
        )


class LimitOffset(Base):
    def __init__(self, root, limit):
        self.root = root
        self.limit = limit
        self.offset = None

    def Offset(self, offset):
        self.offset = offset
        return self

    def render(self):
        result = "%s.limit(%s)" % (self.root.render(), self.limit)
        if self.offset is not None:
            result += ".offset(%s)" % self.offset
        return result
