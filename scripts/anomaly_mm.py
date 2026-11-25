"""Precipitation anomaly map in millimetres.

Shortcut for ``merge-cptec --product anomaly``; run with ``--help`` for all options.
"""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "anomaly", *sys.argv[1:]])
