"""
Entry point: python main.py <command> [options]  (see python main.py --help)

Run without arguments (e.g. Run/Debug in the IDE) to use DEBUG_ARGS below.
"""

import sys

from investmenthelp.cli import main

# Arguments used when the script is started without any (Run/Debug from the IDE)
DEBUG_ARGS = ["scrape", "--start", "0", "--end", "5000", "--threads", "1", "--out", "data/advisors_debug.csv"]

if __name__ == "__main__":
    main(sys.argv[1:] or DEBUG_ARGS)
