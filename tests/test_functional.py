import logging
import unittest

import ddt
from sqlalchemy import and_  # noqa
from sqlalchemy import between  # noqa
from sqlalchemy import select  # noqa
from sqlalchemy import not_  # noqa

from tests import db
from tests.db import foo, bar, wumbo
from sqlitis.convert import to_sqla

LOG = logging.getLogger(__name__)
TABLES = {"foo": foo, "bar": bar, "wumbo": wumbo}


@ddt.ddt
class TestFunctional(unittest.TestCase):

    def setUp(self):
        super(TestFunctional, self).setUp()
        self.engine = db.connect()

    @ddt.file_data('data.json')
    def test_select(self, sql, data=None, output=None, **kwargs):
        if not data:
            self.skipTest("missing data")
        if not output:
            self.skipTest("missing expected output")

        self._prepare_data(data)
        sqla = eval(to_sqla(sql))
        result = self.engine.execute(sqla)
        rows = [list(x) for x in result.fetchall()]
        self.assertEqual(rows, output)

    def _prepare_data(self, data):
        LOG.debug("Preparing test data")
        for table_name, values in data.items():
            LOG.debug('  insert into %s values %s', table_name, values)
            table = TABLES[table_name]
            self.engine.execute(table.insert(), values)
