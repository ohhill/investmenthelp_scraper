"""
investmenthelp.org advisors scraper.

Commands:
  stats        total advisors count and ID range (single request)
  scrape       scrape all advisors into CSV (resumable)
  scan         check each ID in a range for a valid detail page
  parse-html   parse saved browser-rendered detail pages with selectolax

Examples:
  python main.py stats
  python main.py scrape
  python main.py scrape --out data/advisors.csv --rescrape
  python main.py scrape --start 3 --end 5000 --threads 20 --delay 0.5
  python main.py --proxy http://user:pass@host:port scrape
  python main.py scan --start 131170 --end 131190 -v
  python main.py parse-html saved_page.html
"""

import argparse
import json
import os

from investmenthelp import api, scraper
from investmenthelp.parser import parse_detail_html

DEFAULT_OUT = os.path.join("data", "advisors.csv")


def cmd_stats(args):
    count, min_id, max_id = api.get_stats(api.get_session(args.proxy))
    print(f"Total advisors: {count}")
    print(f"ID range:       {min_id} .. {max_id}")
    print(f"Density:        {count / (max_id - min_id + 1):.1%} of IDs in range exist")


def cmd_scrape(args):
    scraper.scrape(
        args.out, proxy=args.proxy, start=args.start, end=args.end, batch=args.batch,
        threads=args.threads, delay=args.delay, rescrape=args.rescrape,
    )


def cmd_scan(args):
    scraper.scan(
        proxy=args.proxy, start=args.start, end=args.end, threads=args.threads, delay=args.delay,
        mode=args.mode, out=args.out, verbose=args.verbose,
    )


def cmd_parse_html(args):
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            print(json.dumps(parse_detail_html(f.read()), indent=2, ensure_ascii=False))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--proxy",
        default=os.environ.get("PROXY"),
        help="http://user:pass@host:port or socks5://host:port (or PROXY env var)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    workers = argparse.ArgumentParser(add_help=False)
    workers.add_argument("--start", type=int, help="first ID")
    workers.add_argument("--end", type=int, help="last ID")
    workers.add_argument("--threads", type=int, default=20)
    workers.add_argument("--delay", type=float, default=0.5, help="delay in seconds after each request, per thread")

    sub.add_parser("stats", help="total count and ID range (single request)")

    p_scrape = sub.add_parser("scrape", parents=[workers], help="scrape advisors into CSV")
    p_scrape.add_argument("--batch", type=int, default=2000, help="advisors per request")
    p_scrape.add_argument("--out", default=DEFAULT_OUT)
    p_scrape.add_argument("--rescrape", action="store_true", help="ignore existing CSV and scrape everything again")

    p_scan = sub.add_parser("scan", parents=[workers], help="check each ID in a range")
    p_scan.add_argument("--mode", choices=["api", "html"], default="api",
                        help="api: advisor exists in GraphQL; html: raw page contains 'Contact Details'")
    p_scan.add_argument("--out", help="file to save valid IDs")
    p_scan.add_argument("-v", "--verbose", action="store_true", help="print every valid ID")

    p_html = sub.add_parser("parse-html", help="parse saved rendered detail pages with selectolax")
    p_html.add_argument("files", nargs="+")

    return parser


COMMANDS = {"stats": cmd_stats, "scrape": cmd_scrape, "scan": cmd_scan, "parse-html": cmd_parse_html}


def main(argv=None):
    args = build_parser().parse_args(argv)
    COMMANDS[args.cmd](args)
