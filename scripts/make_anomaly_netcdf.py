"""Compute the precipitation anomaly and save it as NetCDF.

Shortcut for ``merge-cptec --product anomaly-netcdf``; run with ``--help`` for all options.
"""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "anomaly-netcdf", *sys.argv[1:]])
