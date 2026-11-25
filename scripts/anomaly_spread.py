"""Precipitation anomaly map in classes of spatial standard deviation.

Shortcut for ``merge-cptec --product anomaly-spread``; run with ``--help`` for all options.
"""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "anomaly-spread", *sys.argv[1:]])
