import logging
from pprint import pprint as print

import sqlglot
import sqlglot.expressions as E

LOG = logging.getLogger(__name__)


def to_sqla(sql):
    sql = sql.strip()
    if not sql:
        raise Exception("Empty SQL string provided")

    tree = sqlglot.parse(sql)[0]

    LOG.debug(tree)

    select = Select(tree)
    return select.render()


def convert_column(col, table=None):
    """Turns foo.id into foo.c.id. If a table is given, then id becomes <table>.c.id"""
    if "." in col and table and not col.startswith(table + "."):
        raise Exception("field %s invalid for table %s" % (col, table))
    elif "." in col:
        if col.count(".") > 1:
            raise Exception("field '%s' invalid (too many '.')" % col)
        return ".c.".join(col.split("."))
    elif "." not in col and table:
        return "%s.c.%s" % (table, col)
    else:
        return "text('%s')" % col


class Select:
    def __init__(self, tree):
        self.tree = tree

        self.columns = []
        self.select_star = False
        self.table_names = []
        self.join_table_names = []

        def handle_column(col, alias=None):
            if type(col) is E.Star:
                self.select_star = True
                return

            # Use the raw column name ('id' or 'foo.id') to handle table aliases.
            col_name = col.sql(dialect="mysql")
            if not alias:
                return

            elif col_name:
                self.column_names.append(col_name)

        # Column names
        #   select *
        #   select col1, col2
        #   select *, col1, col2
        for expr in self.tree.args["expressions"]:
            if type(expr) in [E.Column, E.Alias]:
                if type(expr.this) is E.Star:
                    self.select_star = True
                else:
                    self.columns.append(Column(expr))

        # Table names
        #   from tbl
        #   from tbl1, tbl2
        from_args = []
        if self.tree.args["from"]:
            from_args = self.tree.args["from"].args["expressions"]
        for expr in from_args:
            if type(expr) is E.Table:
                table = expr.this
                if type(table) is E.Identifier:
                    tbl_name = table.this
                    table_names = self.table_names.append(tbl_name)

        # Joins
        #   from tbl1, tbl2             -- a cross join
        #   from tbl1 cross join tbl2
        #   from tbl1 join tbl2         -- an inner join
        #   from tbl1 inner join tbl2
        join_args = []
        for join in self.tree.args["joins"]:
            print(join.args)
            if type(join.this) is E.Table:
                table = join.this
                if type(table.this) is E.Identifier:
                    tbl_name = table.this.this

                    kind = join.args["kind"]
                    if kind == "cross":
                        table_names = self.table_names.append(tbl_name)
                    elif kind == "inner":
                        self.join_table_names.append(tbl_name)
                    else:
                        raise Exception(f"unhandled join kind={kind}")

    def render(self):
        # select * from foo -->  select([foo])
        # select * from foo, bar -->  select([foo, bar])
        # select * from foo cross join bar -->  select([foo, bar])
        cols = []

        select_from = ""
        if self.select_star and self.join_table_names:
            # select * from foo join bar -->  select([foo.join(bar)])
            # (Assume we join with the last table name)
            cols.extend(self.table_names[:-1])
            cols.append(self.render_joined_tables())
        elif self.select_star:
            # select * from foo, bar -->  select([foo, bar])
            cols.extend(self.table_names)
            cols.extend(self.column_name_list())
        elif self.join_table_names:
            # TODO: select foo.id from foo, b, c join d --> select([foo.c.id]).select_from(foo.join(bar))
            #   -- where do table names go?
            # select foo.id from a foo join bar --> select([foo.c.id]).select_from(foo.join(bar))
            cols.extend(self.table_names[:-1])
            select_from = self.render_joined_tables()
        else:
            # select foo.id from foo, bar --> select([foo, bar, foo.id])
            cols.extend(self.column_name_list())

        col_names = ("[%s]" % ", ".join(cols)) if cols else ""
        result = "select(%s)" % col_names
        if select_from:
            result += ".select_from(%s)" % select_from
        return result

    def column_name_list(self):
        cols = []

        tbl = None
        if len(self.table_names) == 1:
            # Only if there's ONE table, do the `<tbl>.c.<col>` conversion
            tbl = self.table_names[0]

        print(self.columns)
        # foo.id AS the_id --> foo.c.id.label('the_id')
        for col in self.columns:
            name = convert_column(col.name, tbl)
            if col.alias:
                name += ".label(%r)" % col.alias
            cols.append(name)

        return cols

    def table_names(self):
        # select * from foo      --> select([foo])
        # select * from foo, bar --> select([foo, bar])

        if not self.select_star:
            return []

        tables = []

        if not self.join_table_names:
            tables.extend(self.table_names)
            return tables

        if self.select_star:
            if self.join_table_names:
                tables
            tables.extend(self.table_names)

        # table_names contains one or more tables
        # POC: assume the last table is the one joined with subsequent tables.
        # but probably this can get more complicated
        if not self.table_names:
            return ""

    def render_joined_tables(self):
        # select * from a, b, c join d --> select([a, b, c.join(d)])
        joined = self.table_names[-1]
        for join in self.join_table_names:
            joined += ".join(%s)" % join
        return joined


class Column:
    def __init__(self, tree):
        self.name = None
        self.alias = None

        if type(tree) is E.Alias:
            self.name = tree.this.sql()
            self.alias = tree.alias.sql()
        else:
            self.name = tree.sql()

    def __repr__(self):
        return "Column%s" % vars(self)
