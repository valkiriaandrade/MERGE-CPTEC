"""Monthly accumulated precipitation map for northern Brazil.

Shortcut for ``merge-cptec --product accumulation --region north``; run with ``--help`` for all options.
"""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "accumulation", "--region", "north", *sys.argv[1:]])
