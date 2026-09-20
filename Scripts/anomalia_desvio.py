"""Entrada compatível por nome; consulte --help para configurar os arquivos."""

import sys

from merge_cptec.cli import main

if __name__ == "__main__":
    main(["--product", "anomaly-spread"] + sys.argv[1:])
