<div align="center">

# 🔎 investmenthelp.org Advisors Scraper

**Collects contact details of every financial advisor listed on
[investmenthelp.org](https://investmenthelp.org) into a clean CSV file.**

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![hrequests](https://img.shields.io/badge/http-hrequests-5A67D8)](https://github.com/daijro/hrequests)
[![selectolax](https://img.shields.io/badge/parser-selectolax-2F855A)](https://github.com/rushter/selectolax)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](#-tests)

| 👥 **120,785** advisors | ⚡ **~75** requests for the full site | 🔁 **Resumable** runs | 🌐 **Proxy** support |
|:---:|:---:|:---:|:---:|

</div>

---

## 📑 Contents

- [Features](#-features)
- [How it works](#-how-it-works)
- [Quick start](#-quick-start)
- [Usage](#-usage)
- [Output](#-output)
- [Project structure](#-project-structure)
- [Tests](#-tests)
- [Disclaimer](#-disclaimer)

## ✨ Features

- **⚡ Fast.** Fetches 2,000 advisors per request instead of crawling one page at a time.
- **🔁 Resumable.** A rerun downloads only the advisors that are not in the CSV yet. `--rescrape` starts over.
- **💾 Crash-safe.** Each batch is written to disk as soon as it arrives.
- **✅ Self-checking.** At the end, the CSV is compared with the list of advisors on the site.
- **🧵 Configurable.** Thread count, delay between requests and an HTTP/SOCKS proxy.
- **🧩 HTML parser.** A [selectolax](https://github.com/rushter/selectolax) parser for pages saved from a browser.
- **🐞 IDE-friendly.** Press Run/Debug on `main.py`, no command-line arguments needed.

## 🧠 How it works

Advisor pages (`/advisor/detail/<id>`) are part of a Vue single-page app. The HTML returned by the
server is the same empty shell for every ID, and the **Contact Details** block is rendered in the browser
from the site's GraphQL endpoint `/v1/graphql`. The scraper queries that endpoint directly, the same way
the page does, so no browser is needed.

```mermaid
flowchart LR
    A["📋 List all advisor IDs<br/>10,000 per request"] --> B{"Already in CSV?"}
    B -->|yes| S["⏭ Skip"]
    B -->|"no, or --rescrape"| C["📦 Split into batches<br/>2,000 IDs each"]
    C --> D["🧵 Fetch in parallel<br/>threads + delay + proxy"]
    D --> E["💾 Append to CSV<br/>after every batch"]
    E --> F["✅ Sort, deduplicate<br/>and verify completeness"]
```

<details>
<summary><b>Why not just iterate over IDs 1, 2, 3 …?</b></summary>
<br>

The ID in the URL (`cst_no`) is a customer number from the institute's CRM, not an advisor counter.
Numbers are also assigned to people who are not advisors, so only **~43%** of the IDs between the lowest
and the highest one belong to advisors:

| ID range | Share of IDs that are advisors |
|---|---|
| 0 – 19,999 | 38% |
| 20,000 – 79,999 | ~10% |
| 75,235 – 100,002 | 0% (unused block) |
| 100,000 – 199,999 | 89 – 97% |
| 200,000 – 282,504 | 4 – 38% |

| Approach | Requests | Empty responses |
|---|---|---|
| Crawl every ID from 1 to 282,504 | ~282,500 | ~162,000 |
| **This scraper:** list IDs, then fetch in batches | **~75** | **0** |

</details>

## 🚀 Quick start

```bash
git clone <repo-url> && cd investmenthelp_scraper
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py stats     # how many advisors are there?
python main.py scrape    # scrape them all into data/advisors.csv
```

> [!NOTE]
> `hrequests` may print `Please run pip install hrequests[all] for automated browsing support`.
> You can ignore it: browser automation is not used.

## 📖 Usage

All commands run through `main.py`. Run `python main.py <command> --help` for details.

| Command | Description |
|---|---|
| `stats` | Total advisors count and ID range (single request) |
| `scrape` | Scrape all advisors into CSV (resumable) |
| `scan` | Check each ID in a range for a valid detail page |
| `parse-html` | Parse saved browser-rendered pages with selectolax |

### 📥 Scrape advisors

```bash
python main.py scrape
```

| Option | Default | Description |
|---|---|---|
| `--out` | `data/advisors.csv` | Output CSV file |
| `--start` / `--end` | no limit | Only scrape advisors with IDs in this range |
| `--batch` | `2000` | Advisors per request |
| `--threads` | `20` | Parallel requests |
| `--delay` | `0.5` | Pause in seconds after each request, per thread |
| `--rescrape` | off | Ignore the existing CSV and scrape everything again |

<details>
<summary><b>Example output</b></summary>

```text
Advisors on site (in range): 120785  already scraped: 7764  to scrape: 113021
57 requests, threads=20, delay=0.5s, proxy=yes
progress 10/57
progress 20/57
...
progress 57/57

Saved 120785 advisors to data/advisors.csv
All advisors in range are scraped
```

</details>

> [!TIP]
> If some requests fail, the summary ends with `Missing N advisors`. Run the same command again to fetch
> only the missing ones.

### 📊 Count advisors and check IDs

```bash
python main.py stats
python main.py scan --start 131170 --end 131190 -v
```

`scan` checks IDs one by one. It takes the same `--start / --end / --threads / --delay` options, plus
`--out` to save the valid IDs. It is meant for spot checks; `scrape` does not need it.

### 🧩 Parse a saved page

`investmenthelp.parser.parse_detail_html()` extracts the same fields from a page rendered and saved
in a browser:

```bash
python main.py parse-html saved_page.html
```

### 🌐 Proxy

Pass a proxy as an argument or set the `PROXY` environment variable:

```bash
python main.py --proxy http://user:pass@host:port scrape
PROXY=socks5://host:port python main.py scrape
```

> [!WARNING]
> Do not hard-code proxy credentials in the source code.

### 🐞 Debugging in an IDE

When `main.py` is started without arguments (Run/Debug in PyCharm or VS Code), it uses the `DEBUG_ARGS`
list at the top of the file:

```python
DEBUG_ARGS = ["scrape", "--start", "0", "--end", "5000", "--threads", "1", "--out", "data/advisors_debug.csv"]
```

By default this scrapes a small ID range in a single thread into a separate file. Edit the list to debug
other scenarios.

## 📄 Output

`data/advisors.csv`: one row per advisor, sorted by ID. The example values below are fictional.

| Column | Example | Filled |
|---|---|---:|
| `cst_no` | `12345` | 100% |
| `first_name`, `last_name` | `John`, `Sample` | 99% |
| `prefix`, `title` | `Mr.`, `Senior Vice President` | 33%, 40% |
| `organization` | `Acme Wealth` | 1% |
| `email` | `john.sample@example.com` | 93% |
| `phone` | `555-010-0000` | 71% |
| `website` | | 0% |
| `address` | `100 Main Street, Suite 200` | 77% |
| `city`, `state`, `postal_code`, `country` | `Springfield`, `IL`, `62701`, `UNITED STATES` | 76–78% |
| `location` | `Springfield, IL` | 78% |
| `url` | `https://investmenthelp.org/advisor/detail/12345` | 100% |

*Filled* is the share of advisors with a value in a full run. `website` is kept for completeness, but the site currently has no websites.

> [!IMPORTANT]
> **Data quality.** Values are saved exactly as the site stores them; an empty field means the site has
> no value either. Validate and deduplicate the data before use:
> - **Duplicates:** some people have several IDs, and some emails are shared (~1,200 emails appear more than once).
> - **Junk records:** hundreds of rows with the same fake email, created by a vulnerability scanner.
> - **Placeholders:** values such as `00000` in address fields.
> - **Organization:** `organization` is rarely filled; the firm name is often the first line of `address`.

## 📁 Project structure

```text
investmenthelp_scraper/
├── investmenthelp/
│   ├── api.py          # GraphQL client: sessions, retries, ID listing, fetching, normalize()
│   ├── parser.py       # parse_detail_html(): selectolax parser for rendered pages
│   ├── storage.py      # CSV: load, append, sort
│   ├── scraper.py      # workflows: resumable scrape(), per-ID scan()
│   └── cli.py          # command line interface
├── tests/
│   ├── fixtures/
│   │   └── advisor_detail.html   # anonymized rendered detail page
│   ├── test_parser.py
│   └── test_normalize.py
├── data/               # scraped CSV files (git-ignored)
├── main.py             # entry point + DEBUG_ARGS for IDE runs
├── requirements.txt
└── requirements-dev.txt
```

## 🧪 Tests

Tests run offline and make no network requests:

```bash
pip install -r requirements-dev.txt
pytest
```

## 📜 Disclaimer

This project is for educational and research purposes. Respect the website's terms of use, keep request
rates reasonable, and handle the collected personal data in line with applicable laws (e.g. GDPR, CAN-SPAM).
