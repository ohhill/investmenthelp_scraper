"""
Scraping workflows.

scrape(): lists all existing advisor IDs, skips those already in the CSV (unless rescrape),
fetches the rest in parallel batches and appends each batch to the CSV right away,
so an interrupted run can simply be restarted.

scan(): checks every ID in a range one by one (validity of /advisor/detail/<id> pages).
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from investmenthelp import api, storage


def scrape(out, proxy=None, start=None, end=None, batch=2000, threads=20, delay=0.5, rescrape=False):
    rescrape = rescrape or not os.path.exists(out)
    done_ids = set() if rescrape else set(storage.load_csv(out))

    start = start if start is not None else 0
    end = end if end is not None else float("inf")
    all_ids = [i for i in api.iter_all_ids(api.get_session(proxy)) if start <= i <= end]
    todo = [i for i in all_ids if i not in done_ids]
    batches = [todo[i:i + batch] for i in range(0, len(todo), batch)]

    print(f"Advisors on site (in range): {len(all_ids)}  already scraped: {len(all_ids) - len(todo)}  "
          f"to scrape: {len(todo)}{'  (rescrape)' if rescrape else ''}")
    print(f"{len(batches)} requests, threads={threads}, delay={delay}s, proxy={'yes' if proxy else 'none'}")

    def fetch(ids):
        return api.with_retries(
            lambda: api.fetch_advisors(api.get_session(proxy), ids), f"{ids[0]}..{ids[-1]}", delay
        )

    failed = 0
    f, writer = storage.open_writer(out, overwrite=rescrape)
    with f, ThreadPoolExecutor(max_workers=threads) as pool:
        futures = {pool.submit(fetch, b): b for b in batches}
        for done, fut in enumerate(as_completed(futures), 1):
            b = futures[fut]
            try:
                writer.writerows(fut.result())
                f.flush()
            except Exception as exc:
                failed += 1
                print(f"ERROR   batch {b[0]}..{b[-1]}: {exc}", flush=True)
            if done % 10 == 0 or done == len(batches):
                print(f"progress {done}/{len(batches)}", flush=True)

    rows = storage.load_csv(out)
    storage.save_sorted(out, rows)
    missing = [i for i in all_ids if i not in rows]
    print(f"\nSaved {len(rows)} advisors to {out}")
    if missing:
        print(f"Missing {len(missing)} advisors ({failed} failed requests) - run again to fetch them")
    else:
        print("All advisors in range are scraped")
    return missing


def scan(proxy=None, start=None, end=None, threads=20, delay=0.5, mode="api", out=None, verbose=False):
    if start is None or end is None:
        _, min_id, max_id = api.get_stats(api.get_session(proxy))
        start = min_id if start is None else start
        end = max_id if end is None else end

    check = api.advisor_exists if mode == "api" else api.page_has_marker
    ids = range(start, end + 1)
    print(f"Scanning {len(ids)} IDs ({start}..{end}), mode={mode}, "
          f"threads={threads}, delay={delay}s, proxy={'yes' if proxy else 'none'}")

    def is_valid(cst_no):
        return api.with_retries(lambda: check(api.get_session(proxy), cst_no), str(cst_no), delay)

    valid, errors = [], []
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = {pool.submit(is_valid, i): i for i in ids}
        for done, fut in enumerate(as_completed(futures), 1):
            cst_no = futures[fut]
            try:
                if fut.result():
                    valid.append(cst_no)
                    if verbose:
                        print(f"VALID   {api.DETAIL_URL.format(cst_no)}", flush=True)
            except Exception as e:
                errors.append(cst_no)
                print(f"ERROR   {cst_no}: {e}", flush=True)
            if done % 1000 == 0:
                print(f"progress {done}/{len(ids)}  valid={len(valid)}  errors={len(errors)}", flush=True)

    valid.sort()
    print(f"\nChecked: {len(ids)}  valid: {len(valid)}  errors: {len(errors)}")
    if valid:
        print(f"Valid ID range: {valid[0]} .. {valid[-1]}")
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w") as f:
            f.writelines(f"{i}\n" for i in valid)
        print(f"Saved valid IDs to {out}")
    return valid
