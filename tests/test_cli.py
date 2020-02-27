import logging
import os
import subprocess
import unittest

import ddt

LOG = logging.getLogger(__name__)
CLI_NAME = "sqlitis"


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    out, err = out.decode("utf-8"), err.decode("utf-8")
    ret = p.returncode
    if ret != 0:
        LOG.error("Command %s failed [exited %s]", cmd, ret)
        LOG.error("STDOUT:\n%s", out)
        LOG.error("STDERR:\n%s", err)
    return ret, out, err


@ddt.ddt
class TestSqlitisCLI(unittest.TestCase):
    @ddt.file_data("cli_data.yaml")
    def test_cli(self, sql, exitcode, stdout, stderr):
        # We have '\n' in the YAML file, but '\r\n' is printed on Windows.
        stdout = stdout.replace("\n", os.linesep)
        stderr = stderr.replace("\n", os.linesep)
        ret, out, err = run_cmd(["sqlitis", sql])
        self.assertEqual(ret, exitcode)
        self.assertEqual(out, stdout)
        self.assertEqual(err, stderr)
