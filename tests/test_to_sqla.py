import logging
import unittest

from sqlitis.convert import to_sqla

import ddt
import sqlparse

LOG = logging.getLogger(__name__)


@ddt.ddt
class TestToSqla(unittest.TestCase):
    @ddt.file_data("data.yaml")
    def test_to_sqla(self, sql, sqla, exception=None, *args, **kwargs):
        if not isinstance(sql, list):
            sql = [sql]
        for s in sql:
            self._run(s, sqla, exception)

    def _run(self, sql, sqla, exception):
        LOG.debug("sql: '%s'", sql)

        x = sqlparse.parse(sql)[0]
        for x in x.tokens:
            if not x.is_whitespace:
                LOG.debug("  %r %s", x, type(x))

        try:
            actual_sqla = to_sqla(sql)
        except Exception as e:
            if not exception:
                raise
            self.assertRegex(str(e), exception.strip())
        else:
            self.assertEqual(actual_sqla, sqla)
