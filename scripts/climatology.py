"""Precipitation climatology map.

Shortcut for ``merge-cptec --product climatology``; run with ``--help`` for all options.
"""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "climatology", *sys.argv[1:]])
