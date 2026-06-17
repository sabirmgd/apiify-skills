#!/usr/bin/env python3
"""YC company lead-list extractor.

Strategy:
  1. Load the public YC company directory page and extract window.AlgoliaOpts.
  2. Query the YC Algolia index directly for company search results.
  3. Optionally enrich each hit from its public YC company profile page.

This is a public-directory lead-list demo. It does not scrape private emails,
phones, or gated data.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests


BASE = "https://www.ycombinator.com"
INDEX_BY_RELEVANCE = "YCCompany_production"
INDEX_BY_LAUNCH_DATE = "YCCompany_By_Launch_Date_production"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)


class ApiifyError(RuntimeError):
    pass


def request_text(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=30)
    if response.status_code >= 400:
        raise ApiifyError(f"GET {url} failed with HTTP {response.status_code}")
    return response.text


def discover_algolia_opts(session: requests.Session) -> dict[str, str]:
    html_text = request_text(session, f"{BASE}/companies")
    match = re.search(r"window\.AlgoliaOpts\s*=\s*(\{.*?\});", html_text, re.S)
    if not match:
        raise ApiifyError("Could not find window.AlgoliaOpts on the YC companies page")
    opts = json.loads(match.group(1))
    if not opts.get("app") or not opts.get("key"):
        raise ApiifyError("Algolia opts did not include app/key")
    return {"app": opts["app"], "key": opts["key"]}


def search_companies(
    session: requests.Session,
    opts: dict[str, str],
    *,
    query: str,
    page: int,
    hits_per_page: int,
    sort: str,
) -> dict[str, Any]:
    index = INDEX_BY_LAUNCH_DATE if sort == "launch_date" else INDEX_BY_RELEVANCE
    app = opts["app"]
    url = f"https://{app.lower()}-dsn.algolia.net/1/indexes/{index}/query"
    headers = {
        "x-algolia-application-id": app,
        "x-algolia-api-key": opts["key"],
        "content-type": "application/json",
        "accept": "application/json",
    }
    body = {
        "query": query,
        "page": page,
        "hitsPerPage": hits_per_page,
    }
    response = session.post(url, headers=headers, json=body, timeout=30)
    if response.status_code >= 400:
        raise ApiifyError(f"Algolia query failed with HTTP {response.status_code}")
    return response.json()


def extract_json_after(text: str, marker: str) -> Any | None:
    start = text.find(marker)
    if start == -1:
        return None
    brace = text.find("{", start + len(marker))
    if brace == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(brace, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[brace : idx + 1])
    return None


def extract_array_after(text: str, marker: str) -> Any | None:
    start = text.find(marker)
    if start == -1:
        return None
    bracket = text.find("[", start + len(marker))
    if bracket == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(bracket, len(text)):
        char = text[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[bracket : idx + 1])
    return None


def enrich_company(session: requests.Session, slug: str) -> dict[str, Any]:
    profile_url = f"{BASE}/companies/{slug}"
    raw = request_text(session, profile_url)
    decoded = html.unescape(raw)
    company = extract_json_after(decoded, '"company":') or {}
    founders = extract_array_after(decoded, '"founders":') or []

    return {
        "profile_url": profile_url,
        "company_linkedin_url": company.get("linkedin_url"),
        "company_twitter_url": company.get("twitter_url"),
        "company_facebook_url": company.get("fb_url"),
        "company_github_url": company.get("github_url"),
        "year_founded": company.get("year_founded"),
        "founders": [
            {
                "name": founder.get("full_name"),
                "title": founder.get("title"),
                "linkedin_url": founder.get("linkedin_url"),
                "twitter_url": founder.get("twitter_url"),
                "github_url": founder.get("github_url"),
                "profile_url": founder.get("url"),
            }
            for founder in founders
        ],
    }


def normalize_hit(hit: dict[str, Any]) -> dict[str, Any]:
    slug = hit.get("slug")
    return {
        "name": hit.get("name"),
        "slug": slug,
        "yc_url": f"{BASE}/companies/{slug}" if slug else None,
        "website": hit.get("website"),
        "one_liner": hit.get("one_liner"),
        "long_description": hit.get("long_description"),
        "batch": hit.get("batch"),
        "status": hit.get("status"),
        "industry": hit.get("industry"),
        "subindustry": hit.get("subindustry"),
        "industries": hit.get("industries") or [],
        "regions": hit.get("regions") or [],
        "all_locations": hit.get("all_locations"),
        "team_size": hit.get("team_size"),
        "is_hiring": hit.get("isHiring"),
        "nonprofit": hit.get("nonprofit"),
        "top_company": hit.get("top_company"),
        "tags": hit.get("tags") or [],
        "objectID": hit.get("objectID"),
    }


def collect(args: argparse.Namespace) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"user-agent": USER_AGENT})

    opts = discover_algolia_opts(session)
    remaining = args.limit
    page = args.page
    items: list[dict[str, Any]] = []
    first_response: dict[str, Any] | None = None

    while remaining > 0:
        hits_per_page = min(max(remaining, 1), 100)
        response = search_companies(
            session,
            opts,
            query=args.query,
            page=page,
            hits_per_page=hits_per_page,
            sort=args.sort,
        )
        first_response = first_response or response
        hits = response.get("hits") or []
        if not hits:
            break

        for hit in hits:
            row = normalize_hit(hit)
            if args.enrich and row.get("slug"):
                try:
                    row.update(enrich_company(session, row["slug"]))
                except Exception as exc:
                    row["enrichment_error"] = str(exc)
                if args.enrich_delay:
                    time.sleep(args.enrich_delay)
            items.append(row)
            remaining -= 1
            if remaining <= 0:
                break

        page += 1
        if page >= response.get("nbPages", 0):
            break

    return {
        "source": "ycombinator.com/companies",
        "query": args.query,
        "count": len(items),
        "nbHits": first_response.get("nbHits") if first_response else None,
        "page_start": args.page,
        "sort": args.sort,
        "enriched": args.enrich,
        "items": items,
    }


def csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def write_csv(items: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "name",
        "website",
        "yc_url",
        "one_liner",
        "batch",
        "industry",
        "subindustry",
        "industries",
        "regions",
        "all_locations",
        "team_size",
        "is_hiring",
        "top_company",
        "tags",
        "company_linkedin_url",
        "company_twitter_url",
        "company_github_url",
        "year_founded",
        "founders",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow({field: csv_value(item.get(field)) for field in fields})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export YC company directory leads.")
    parser.add_argument("--query", default="", help="Search query, e.g. 'ai agents'.")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--page", type=int, default=0)
    parser.add_argument(
        "--sort",
        choices=["relevance", "launch_date"],
        default="relevance",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Fetch each public YC company profile page for founders/social links.",
    )
    parser.add_argument("--enrich-delay", type=float, default=0.2)
    parser.add_argument("--output", help="Write JSON output to this file.")
    parser.add_argument("--csv-output", help="Write CSV output to this file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        payload = collect(args)
    except ApiifyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if args.csv_output:
        write_csv(payload["items"], Path(args.csv_output))

    output = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n")
    else:
        print(output)


if __name__ == "__main__":
    main()
