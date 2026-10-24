"""Build the frozen arXiv sampling frame for the TO literature screen.

Queries the arXiv API, keeps entries first submitted 2015-01-01..2026-10-22,
and writes tasks/arxiv_frame_20261022.json with a hash-based frozen order.

Usage: python build_arxiv_frame.py
Stdlib only. Sequential requests with a 3 s pause between arXiv calls.
"""
import datetime as dt
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

API = "http://export.arxiv.org/api/query"
SEARCH_QUERY = 'all:"topology optimization" AND (all:compliance OR all:stiffness)'
PAGE = 200
PAUSE_S = 3.0
SALT = "20261022:"
DATE_MIN = "2015-01-01"
DATE_MAX = "2026-10-22"
UA = "python-urllib/3 (literature-screen script)"
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}
OUT = Path(__file__).resolve().parents[1] / "arxiv_frame_20261022.json"


def fetch(start: int) -> bytes:
    params = {
        "search_query": SEARCH_QUERY,
        "start": str(start),
        "max_results": str(PAGE),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            wait = PAUSE_S * (2 ** attempt)
            print(f"start={start} attempt {attempt}: {e}; retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"arXiv request failed repeatedly at start={start}")


def versionless(abs_url: str) -> str:
    m = re.search(r"arxiv\.org/abs/(.+)$", abs_url.strip())
    if not m:
        raise ValueError(f"unexpected id URL: {abs_url}")
    return re.sub(r"v\d+$", "", m.group(1))


def parse(xml: bytes):
    root = ET.fromstring(xml)
    total = int(root.find("os:totalResults", NS).text)
    entries = []
    for e in root.findall("a:entry", NS):
        id_el = e.find("a:id", NS)
        if id_el is None or "arxiv.org/abs/" not in id_el.text:
            continue  # error entry
        prim = e.find("arxiv:primary_category", NS)
        entries.append({
            "id": versionless(id_el.text),
            "title": " ".join(e.find("a:title", NS).text.split()),
            "published": e.find("a:published", NS).text.strip(),
            "primary_category": prim.get("term") if prim is not None else "unknown",
        })
    return total, entries


def main():
    retrieved = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    raw, total_reported, start, empty_pages = [], None, 0, 0
    while True:
        total, entries = parse(fetch(start))
        total_reported = total if total_reported is None else total_reported
        print(f"start={start}: {len(entries)} entries (totalResults={total})", file=sys.stderr)
        if not entries:
            empty_pages += 1
            # arXiv occasionally returns an empty page transiently; retry a few times.
            if start < total_reported and empty_pages <= 3:
                time.sleep(PAUSE_S * 3)
                continue
            break
        empty_pages = 0
        raw.extend(entries)
        start += PAGE
        if start >= total_reported:
            break
        time.sleep(PAUSE_S)

    by_id = {}
    for e in raw:
        by_id.setdefault(e["id"], e)
    kept = []
    for e in by_id.values():
        d = e["published"][:10]
        if DATE_MIN <= d <= DATE_MAX:
            kept.append({
                "id": e["id"],
                "title": e["title"],
                "first_submitted": d,
                "primary_category": e["primary_category"],
            })
    for e in kept:
        e["order_key"] = hashlib.sha256((SALT + e["id"]).encode("utf-8")).hexdigest()
    kept.sort(key=lambda e: e["order_key"])

    out = {
        "api_endpoint": API,
        "search_query": SEARCH_QUERY,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "page_size": PAGE,
        "retrieved_utc": retrieved,
        "api_totalResults": total_reported,
        "entries_retrieved": len(raw),
        "unique_ids_retrieved": len(by_id),
        "date_filter": {"field": "published (first submitted, v1)", "min": DATE_MIN, "max": DATE_MAX},
        "n_in_frame": len(kept),
        "frozen_order_rule": 'ascending hex of sha256("20261022:" + versionless_id)',
        "frozen_order": [e["id"] for e in kept],
        "entries": kept,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT}: {len(kept)} entries in frame", file=sys.stderr)


if __name__ == "__main__":
    main()
