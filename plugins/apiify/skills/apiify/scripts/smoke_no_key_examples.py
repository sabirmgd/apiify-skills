#!/usr/bin/env python3
"""Live smoke checks for no-key Apiify example sources.

This intentionally stays out of CI because it touches external services and can
fail due to network/rate-limit noise. Run it before publishing example changes.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any


DEFAULT_USER_AGENT = "apiify-skills-example/0.1 (https://github.com/sabirmgd/apiify-skills)"
SEC_USER_AGENT = "apiify-skills-example/0.1 contact@example.com"


class SmokeError(RuntimeError):
    pass


class ScriptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.scripts: list[str] = []
        self.metas: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag == "meta":
            name = values.get("name") or values.get("property")
            content = values.get("content")
            if name and content:
                self.metas.append((name, content))


def fetch(url: str, *, accept: str = "*/*", user_agent: str = DEFAULT_USER_AGENT) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "accept": accept,
            "accept-language": "en",
            "user-agent": user_agent,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status >= 400:
            raise SmokeError(f"HTTP {response.status} for {url}")
        return response.read()


def fetch_json(url: str) -> Any:
    return json.loads(fetch(url, accept="application/json"))


def fetch_xml(url: str) -> ET.Element:
    return ET.fromstring(fetch(url, accept="application/xml,text/xml,*/*"))


def check_openstreetmap_local_leads() -> None:
    query = urllib.parse.urlencode(
        {
            "q": "dentist Austin Texas",
            "format": "jsonv2",
            "addressdetails": "1",
            "limit": "2",
        }
    )
    rows = fetch_json(f"https://nominatim.openstreetmap.org/search?{query}")
    if not isinstance(rows, list) or not rows:
        raise SmokeError("Nominatim returned no rows")


def check_public_site_technographics() -> None:
    html = fetch("https://www.shopify.com", accept="text/html").decode("utf-8", "replace")
    parser = ScriptParser()
    parser.feed(html)
    if not parser.scripts and not parser.metas:
        raise SmokeError("public-site-technographics found no scripts or meta tags")


def check_hacker_news_market_mentions() -> None:
    query = urllib.parse.urlencode({"query": "ai agents", "tags": "story", "hitsPerPage": "2"})
    payload = fetch_json(f"https://hn.algolia.com/api/v1/search?{query}")
    if not payload.get("hits"):
        raise SmokeError("HN Algolia returned no hits")


def check_rss_feed_monitor() -> None:
    root = fetch_xml("https://www.ycombinator.com/blog/rss")
    if not root.findall(".//item"):
        raise SmokeError("RSS feed returned no items")


def check_lever_hiring_signals() -> None:
    payload = fetch_json("https://api.lever.co/v0/postings/anchorage?mode=json&limit=2")
    if not isinstance(payload, list) or not payload:
        raise SmokeError("Lever returned no postings")


def check_greenhouse_hiring_signals() -> None:
    payload = fetch_json("https://boards-api.greenhouse.io/v1/boards/airbnb/jobs?content=true")
    if not payload.get("jobs"):
        raise SmokeError("Greenhouse returned no jobs")


def check_sec_company_facts() -> None:
    payload = json.loads(
        fetch(
            "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
            accept="application/json",
            user_agent=SEC_USER_AGENT,
        )
    )
    if payload.get("entityName") != "Apple Inc.":
        raise SmokeError("SEC companyfacts did not return Apple Inc.")


def check_shopify_product_feed_monitor() -> None:
    payload = fetch_json("https://www.allbirds.com/products.json?limit=2")
    if not payload.get("products"):
        raise SmokeError("Shopify products feed returned no products")


def check_wordpress_content_monitor() -> None:
    payload = fetch_json(
        "https://wordpress.org/news/wp-json/wp/v2/posts?per_page=2&_fields=id,date,link,title,excerpt"
    )
    if not isinstance(payload, list) or not payload:
        raise SmokeError("WordPress REST posts returned no posts")


def check_sitemap_content_inventory() -> None:
    root = fetch_xml("https://www.shopify.com/sitemap.xml")
    if "urlset" not in root.tag or not list(root):
        raise SmokeError("Sitemap did not return URL rows")


CHECKS = [
    ("openstreetmap-local-leads", check_openstreetmap_local_leads),
    ("public-site-technographics", check_public_site_technographics),
    ("hacker-news-market-mentions", check_hacker_news_market_mentions),
    ("rss-feed-monitor", check_rss_feed_monitor),
    ("lever-hiring-signals", check_lever_hiring_signals),
    ("greenhouse-hiring-signals", check_greenhouse_hiring_signals),
    ("sec-company-facts", check_sec_company_facts),
    ("shopify-product-feed-monitor", check_shopify_product_feed_monitor),
    ("wordpress-content-monitor", check_wordpress_content_monitor),
    ("sitemap-content-inventory", check_sitemap_content_inventory),
]


def main() -> None:
    failures: list[str] = []
    for name, check in CHECKS:
        try:
            check()
            print(f"PASS {name}")
        except Exception as exc:
            failures.append(f"{name}: {exc}")
            print(f"FAIL {name}: {exc}")

    if failures:
        raise SystemExit(1)
    print(f"PASS smoke checked {len(CHECKS)} no-key examples")


if __name__ == "__main__":
    main()
