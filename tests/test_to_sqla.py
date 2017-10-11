import logging
import unittest

from sqlitis.convert import to_sqla

import ddt
import sqlparse

LOG = logging.getLogger(__name__)


@ddt.ddt
class TestToSqla(unittest.TestCase):

    @ddt.file_data('data.json')
    def test_to_sqla(self, sql, sqla, *args, **kwargs):
        if not isinstance(sql, list):
            sql = [sql]
        for s in sql:
            self._run(s, sqla)

    def _run(self, sql, sqla):
        LOG.debug("sql: '%s'", sql)

        x = sqlparse.parse(sql)[0]
        for x in x.tokens:
            if not x.is_whitespace:
                LOG.debug('  %r %s', x, type(x))

        self.assertEqual(to_sqla(sql), sqla)
