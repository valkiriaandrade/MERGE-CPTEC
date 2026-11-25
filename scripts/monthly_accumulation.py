"""Monthly accumulated precipitation map.

Shortcut for ``merge-cptec --product accumulation``; run with ``--help`` for all options.
"""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "accumulation", *sys.argv[1:]])
