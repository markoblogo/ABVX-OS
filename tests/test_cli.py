from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from abvx_harness import __version__
from abvx_harness.__main__ import main


class CliTests(unittest.TestCase):
    def test_version(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--version"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), f"abvx-os {__version__}")


if __name__ == "__main__":
    unittest.main()
