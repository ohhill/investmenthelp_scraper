"""
Client for the investmenthelp.org GraphQL endpoint.

The /advisor/detail/<id> page is a Vue SPA: its raw HTML is the same empty shell for every ID,
and the "Contact Details" block is rendered from the Hasura GraphQL endpoint (/v1/graphql).
Everything here talks to that endpoint directly, the same way the page does.
"""

import threading
import time

import hrequests

BASE_URL = "https://investmenthelp.org"
GRAPHQL_URL = f"{BASE_URL}/v1/graphql"
DETAIL_URL = BASE_URL + "/advisor/detail/{}"
VALID_MARKER = "Contact Details"

FIELDS = [
    "cst_no",
    "first_name",
    "last_name",
    "prefix",
    "title",
    "organization",
    "email",
    "phone",
    "website",
    "address",
    "city",
    "state",
    "postal_code",
    "country",
    "location",
    "url",
]

ADVISOR_QUERY = """
{{
  advisors(where: {{cst_no: {{_in: [{ids}]}}}}, order_by: {{cst_no: asc}}) {{
    cst_no first_name last_name prefix title org_name email phone website
    address_1 address_2 address_3 city state postal_code country
  }}
}}
"""

_local = threading.local()


def get_session(proxy=None):
    """One hrequests session per thread."""
    if not hasattr(_local, "session"):
        _local.session = hrequests.Session(browser="chrome", proxy=proxy, timeout=30)
    return _local.session


def with_retries(fn, label, delay, retries=3):
    """Call fn(), retrying on errors; sleeps `delay` seconds after every attempt."""
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[retry {attempt}] {label}: {e}", flush=True)
            time.sleep(delay * 2 or 1)
        finally:
            time.sleep(delay)


def graphql(session, query):
    resp = session.post(
        GRAPHQL_URL,
        json={"query": query},
        headers={"content-type": "application/json", "referer": BASE_URL + "/"},
    )
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def get_stats(session):
    """Return (count, min_id, max_id) of all advisors."""
    data = graphql(
        session,
        "{ advisors_aggregate { aggregate { count min { cst_no } max { cst_no } } } }",
    )
    agg = data["advisors_aggregate"]["aggregate"]
    return agg["count"], agg["min"]["cst_no"], agg["max"]["cst_no"]


def iter_all_ids(session, page_size=10000):
    """Yield IDs of all existing advisors in ascending order."""
    last = -1
    while True:
        data = graphql(
            session,
            f"{{ advisors(where: {{cst_no: {{_gt: {last}}}}}, "
            f"order_by: {{cst_no: asc}}, limit: {page_size}) {{ cst_no }} }}",
        )
        rows = data["advisors"]
        if not rows:
            return
        for row in rows:
            yield row["cst_no"]
        last = rows[-1]["cst_no"]


def fetch_advisors(session, ids):
    """Return normalized records for the given IDs (missing IDs are skipped)."""
    data = graphql(session, ADVISOR_QUERY.format(ids=",".join(map(str, ids))))
    return [normalize(a) for a in data["advisors"]]


def advisor_exists(session, cst_no):
    """True if the detail page for this ID shows "Contact Details"."""
    data = graphql(session, f"{{ advisors(where: {{cst_no: {{_eq: {cst_no}}}}}) {{ cst_no }} }}")
    return bool(data["advisors"])


def page_has_marker(session, cst_no):
    """Check the raw detail page HTML for "Contact Details" (never matches while the site is an SPA)."""
    resp = session.get(DETAIL_URL.format(cst_no))
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}")
    return VALID_MARKER in resp.text


def clean(value):
    return " ".join(str(value or "").split())


def make_location(city, state):
    return ", ".join(p for p in (city, state) if p)


def normalize(raw):
    """Convert a raw GraphQL advisor into a flat record with FIELDS keys."""
    city, state = clean(raw["city"]), clean(raw["state"])
    return {
        "cst_no": raw["cst_no"],
        "first_name": clean(raw["first_name"]),
        "last_name": clean(raw["last_name"]),
        "prefix": clean(raw["prefix"]),
        "title": clean(raw["title"]),
        "organization": clean(raw["org_name"]),
        "email": clean(raw["email"]).lower(),
        "phone": clean(raw["phone"]),
        "website": clean(raw["website"]),
        "address": ", ".join(clean(raw[k]) for k in ("address_1", "address_2", "address_3") if clean(raw[k])),
        "city": city,
        "state": state,
        "postal_code": clean(raw["postal_code"]),
        "country": clean(raw["country"]),
        "location": make_location(city, state),
        "url": DETAIL_URL.format(raw["cst_no"]),
    }
