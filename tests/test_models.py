import unittest

from sqlitis.models import Select, Table


class TestModels(unittest.TestCase):

    def test_select_nothing(self):
        m = Select()
        self.assertEqual(m.render(), "select()")

    def test_select_star_from_nothing_raises(self):
        m = Select().Star()
        self.assertRaises(Exception, m.render)

    def test_select_star_from_table(self):
        m = Select().Star().From().Table('foo')
        self.assertEqual(m.render(), 'select([foo])')

    def test_select_unqualified_columns_from_table(self):
        # recognize that column 'id' + table 'foo' = foo.c.id
        m = Select().Columns(['a', 'b']).From().Table('foo')
        self.assertEqual(m.render(), 'select([foo.c.a, foo.c.b])')

    def test_select_qualified_columns_from_table(self):
        m = Select().Columns(['foo.a', 'foo.b']).From().Table('foo')
        self.assertEqual(m.render(), 'select([foo.c.a, foo.c.b])')

    def test_joined_table(self):
        m = Table('A').Join('B')
        self.assertEqual(m.render(), 'A.join(B)')

        m = Table('A').Join('B').Join('C').Join('D')
        self.assertEqual(m.render(), 'A.join(B).join(C).join(D)')

    def test_select_from_joined_table(self):
        m = Select().Columns(['foo.a', 'bar.b']).\
            From().Table('foo').Join('bar')
        self.assertEqual(
            m.render(), 'select([foo.c.a, bar.c.b]).select_from(foo.join(bar))'
        )

    def test_select_from_many_joined_tables(self):
        m = Select().Columns(['foo.a', 'bar.b', 'baz.c', 'wumbo.d']).\
            From().Table('foo').Join('bar').Join('baz').Join('wumbo')
        self.assertEqual(
            m.render(), 'select([foo.c.a, bar.c.b, baz.c.c, wumbo.c.d])'
            '.select_from(foo.join(bar).join(baz).join(wumbo))'
        )

    def test_join_on_condition(self):
        m = Table('foo').Join('bar').\
            On().Field('foo.id').Op('=').Field('bar.foo_id')
        self.assertEqual(m.render(), 'foo.join(bar, foo.c.id == bar.c.foo_id)')

    def test_join_on_condition_and_condition(self):
        m = Table('foo').Join('bar').\
            On().Field('foo.id').Op('=').Field('bar.foo_id').\
            And().Field('foo.val').Op('<>').Field('bar.thing')
        self.assertEqual(
            m.render(), 'foo.join(bar, and_(foo.c.id == bar.c.foo_id, '
            'foo.c.val != bar.c.thing))'
        )

    def test_join_on_condition_join_table(self):
        m = Table('foo').Join('bar').\
            On().Field('foo.id').Op('=').Field('bar.foo_id').\
            Join('wumbo').On().Field('foo.id').Op('=').Field('wumbo.foo_id')
        self.assertEqual(
            m.render(), 'foo.join(bar, foo.c.id == bar.c.foo_id)'
            '.join(wumbo, foo.c.id == wumbo.c.foo_id)'
        )
