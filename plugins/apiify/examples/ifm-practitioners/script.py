#!/usr/bin/env python3
"""IFM practitioner directory extractor.

Runtime model:
  - IFM's listing/detail pages are public but Cloudflare challenges plain HTTP.
  - This script uses agent-browser as a browser-backed runtime.
  - A residential proxy can be supplied through RESIDENTIAL_PROXY_URL.

stdout is JSON only. Progress/debug logs go to stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, quote_plus

import requests


BASE = "https://www.ifm.org"
DEFAULT_SESSION = "ifm-practitioners-api"
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"


class ApiifyError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def parse_agent_browser_value(stdout: str) -> Any:
    text = stdout.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def run_agent_browser(args: argparse.Namespace, command: list[str], *, parse_json: bool = False) -> Any:
    cmd = ["agent-browser", "--session", args.browser_session]
    if args.headed:
        cmd.append("--headed")
    if args.ignore_https_errors:
        cmd.append("--ignore-https-errors")
    if args.proxy:
        cmd += ["--proxy", args.proxy]
    cmd += command
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise ApiifyError(f"agent-browser failed: {' '.join(command)} :: {detail}")
    return parse_agent_browser_value(proc.stdout) if parse_json else proc.stdout


@dataclass(frozen=True)
class Coordinates:
    lat: str
    lon: str
    display_name: str


def geocode(location: str) -> Coordinates:
    response = requests.get(
        GEOCODER_URL,
        params={"q": location, "format": "jsonv2", "limit": 1, "addressdetails": 1},
        headers={"User-Agent": "apiify-plus-ifm-practitioners/1.0"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise ApiifyError(f"geocoder failed with HTTP {response.status_code}: {response.text[:300]}")
    matches = response.json()
    if not matches:
        raise ApiifyError(f"could not geocode location: {location!r}")
    first = matches[0]
    return Coordinates(lat=str(first["lat"]), lon=str(first["lon"]), display_name=str(first.get("display_name") or location))


def build_listing_url(location: str, radius_km: int, page_index: int, coords: Coordinates) -> str:
    lat_lon = f"{coords.lat},{coords.lon}"
    encoded_area = quote(f"{lat_lon}<={radius_km}", safe="")
    query = {
        "geocode": lat_lon,
        "location": location,
        "page": str(page_index),
        "radius": str(radius_km),
    }
    query_string = "&".join(f"{quote_plus(k)}={quote_plus(v)}" for k, v in query.items())
    return f"{BASE}/practitioner-listings/{encoded_area}/{encoded_area}/no-country/469?{query_string}"


LISTING_JS = r"""
(async () => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const abs = (href) => href ? new URL(href, location.href).href : null;
  const clean = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const cards = [...document.querySelectorAll('li.practitioner-card')];
  const items = [];

  for (const card of cards) {
    const button = card.querySelector('button.button-toggle');
    if (button && button.getAttribute('aria-expanded') !== 'true') {
      button.click();
      await sleep(250);
    }

    const links = [...card.querySelectorAll('a[href]')].map((a) => ({
      text: clean(a.textContent),
      href: a.getAttribute('href'),
      absolute: abs(a.getAttribute('href')),
    }));
    const h3s = [...card.querySelectorAll('h3.name')].map((h) => clean(h.textContent)).filter(Boolean);
    const name = h3s[0] || clean((button?.textContent || '').replace(/^Open\s+/, '').replace(/\s+card$/, ''));
    const fullText = card.innerText || '';
    const distanceMatch = fullText.match(/(\d+(?:\.\d+)?)\s+miles\s*\/\s*(\d+(?:\.\d+)?)\s+km/i);
    const detailLink = links.find((link) => /full details/i.test(link.text));
    const emailLink = links.find((link) => /^mailto:/i.test(link.href || ''));
    const phoneLink = links.find((link) => /^tel:/i.test(link.href || ''));
    const websiteLink = links.find((link) =>
      /^https?:/i.test(link.href || '') &&
      !/ifm\.org|google\./i.test(link.absolute || '') &&
      !/maps\.google/i.test(link.absolute || '') &&
      !/cookiebot/i.test(link.absolute || '')
    );
    const scheduleLink = links.find((link) => /schedule/i.test(link.text));

    const bullets = [...card.querySelectorAll('li')]
      .map((li) => clean(li.textContent))
      .filter((text) => text && !/^Open /.test(text) && !/full details/i.test(text));

    let summary = '';
    if (detailLink) {
      const beforeDetail = fullText.split(/See full details/i)[0] || '';
      const lines = beforeDetail.split('\n').map(clean).filter(Boolean);
      const skip = new Set([
        clean(button?.textContent),
        name,
        'OFFERS TELEHEALTH',
        'Schedule a Visit',
        'Call this Practitioner',
      ]);
      summary = lines
        .filter((line) => !skip.has(line))
        .filter((line) => !/^\d+(\.\d+)? miles\s*\//i.test(line))
        .filter((line) => !/^\+?\d/.test(line))
        .filter((line) => !line.includes('@'))
        .filter((line) => !/\.[a-z]{2,}\b/i.test(line))
        .join(' ')
        .slice(0, 1200);
    }

    items.push({
      name,
      profile_url: detailLink ? detailLink.absolute : null,
      distance_miles: distanceMatch ? Number(distanceMatch[1]) : null,
      distance_km: distanceMatch ? Number(distanceMatch[2]) : null,
      phone: phoneLink ? phoneLink.href.replace(/^tel:/i, '') : null,
      email: emailLink ? emailLink.href.replace(/^mailto:/i, '').split('?')[0] : null,
      website: websiteLink ? websiteLink.absolute : null,
      schedule_url: scheduleLink ? scheduleLink.absolute : null,
      offers_telehealth: /OFFERS TELEHEALTH/i.test(fullText),
      card_summary: summary || null,
      card_features: [...new Set(bullets)],
    });
  }

  const bodyText = document.body.innerText || '';
  return {
    url: location.href,
    title: document.title,
    cloudflare_challenge: /Just a moment|security verification|Enable JavaScript and cookies/i.test(document.title + '\n' + bodyText),
    total_text: (bodyText.match(/\d+\s+practices found/i) || [null])[0],
    items,
  };
})()
"""


DETAIL_JS = r"""
(() => {
  const abs = (href) => href ? new URL(href, location.href).href : null;
  const clean = (text) => (text || '').replace(/\s+/g, ' ').trim();
  const main = document.querySelector('main') || document.body;
  const links = [...main.querySelectorAll('a[href]')].map((a) => ({
    text: clean(a.textContent),
    href: a.getAttribute('href'),
    absolute: abs(a.getAttribute('href')),
  }));
  const h1 = clean(main.querySelector('h1')?.textContent);
  const bodyText = main.innerText || '';
  const emailLink = links.find((link) => /^mailto:/i.test(link.href || ''));
  const phoneLink = links.find((link) => /^tel:/i.test(link.href || ''));
  const websiteLink = links.find((link) =>
    /^https?:/i.test(link.href || '') &&
    !/ifm\.org|google\./i.test(link.absolute || '') &&
    !/maps\.google/i.test(link.absolute || '')
  );
  const scheduleLink = links.find((link) => /schedule/i.test(link.text));
  const directionsLink = links.find((link) => /directions/i.test(link.text));

  const sectionList = (headingPattern) => {
    const headings = [...main.querySelectorAll('h2, h3')];
    const heading = headings.find((h) => headingPattern.test(clean(h.textContent)));
    if (!heading) return [];
    const values = [];
    let node = heading.nextElementSibling;
    while (node && !/^H[23]$/.test(node.tagName)) {
      values.push(...[...node.querySelectorAll('li')].map((li) => clean(li.textContent)).filter(Boolean));
      node = node.nextElementSibling;
    }
    return [...new Set(values)];
  };

  const addressMatch = bodyText.match(/Address:\s*([\s\S]*?)\s+Phone:/i);
  const faxMatch = bodyText.match(/Fax:\s*([^\n]+?)\s+Email:/i);
  const updatedMatch = bodyText.match(/Profile last updated\s+([0-9/]+)/i);
  const telehealthMatch = bodyText.match(/Available in\s+(.+?)(?:\n| Call the Practitioner| Email the Practitioner)/i);

  return {
    detail_url: location.href,
    name: h1 || null,
    payment: bodyText.includes('Fee for service / Cash-based') ? 'Fee for service / Cash-based' : null,
    profile_last_updated: updatedMatch ? updatedMatch[1] : null,
    phone: phoneLink ? phoneLink.href.replace(/^tel:/i, '') : null,
    email: emailLink ? emailLink.href.replace(/^mailto:/i, '').split('?')[0] : null,
    website: websiteLink ? websiteLink.absolute : null,
    schedule_url: scheduleLink ? scheduleLink.absolute : null,
    directions_url: directionsLink ? directionsLink.absolute : null,
    address: addressMatch ? clean(addressMatch[1]) : null,
    fax: faxMatch ? clean(faxMatch[1]) : null,
    offers_telehealth: /OFFERS TELEHEALTH|Telehealth Options/i.test(bodyText),
    telehealth_locations: telehealthMatch ? clean(telehealthMatch[1]) : null,
    languages: sectionList(/Languages Spoken/i),
    health_concerns: sectionList(/Health Concerns Addressed/i),
    coursework: sectionList(/IFM Course Work/i),
    qualifications: sectionList(/Graduate School Education|Summary of Qualifications/i),
    professional_associations: sectionList(/Professional Associations/i),
  };
})()
"""


def ensure_loaded(args: argparse.Namespace, url: str, wait_ms: int) -> dict[str, Any]:
    log(f"Opening {url}")
    run_agent_browser(args, ["open", url])
    run_agent_browser(args, ["wait", str(wait_ms)])
    result = run_agent_browser(args, ["eval", LISTING_JS], parse_json=True)
    if not isinstance(result, dict):
        raise ApiifyError("browser extraction did not return a JSON object")
    if result.get("cloudflare_challenge"):
        raise ApiifyError(
            "IFM is showing a Cloudflare/security challenge. "
            "Run once with --headed and/or RESIDENTIAL_PROXY_URL, complete any browser verification, then rerun."
        )
    return result


def enrich_detail(args: argparse.Namespace, item: dict[str, Any], wait_ms: int) -> dict[str, Any]:
    profile_url = item.get("profile_url")
    if not profile_url:
        return item
    log(f"Opening detail: {item.get('name')}")
    run_agent_browser(args, ["open", profile_url])
    run_agent_browser(args, ["wait", str(wait_ms)])
    detail = run_agent_browser(args, ["eval", DETAIL_JS], parse_json=True)
    if isinstance(detail, dict):
        merged = dict(item)
        merged["detail"] = detail
        for key, value in detail.items():
            if value not in (None, "", [], {}) and not merged.get(key):
                merged[key] = value
        return merged
    return item


def parse_total(total_text: str | None) -> int | None:
    if not total_text:
        return None
    match = re.search(r"(\d+)", total_text)
    return int(match.group(1)) if match else None


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.reset_session:
        try:
            run_agent_browser(args, ["close"])
        except ApiifyError:
            pass

    coords = Coordinates(args.lat, args.lon, args.location) if args.lat and args.lon else geocode(args.location)
    all_items: list[dict[str, Any]] = []
    total_available: int | None = None
    pages_seen: list[str] = []

    max_pages = args.pages if args.pages > 0 else 100
    for page_index in range(max_pages):
        if args.limit and len(all_items) >= args.limit:
            break
        url = build_listing_url(args.location, args.radius_km, page_index, coords)
        listing = ensure_loaded(args, url, args.wait_ms)
        pages_seen.append(str(listing.get("url") or url))
        total_available = total_available or parse_total(listing.get("total_text"))
        page_items = listing.get("items") or []
        if not page_items:
            break
        for item in page_items:
            if args.details:
                item = enrich_detail(args, item, args.detail_wait_ms)
            all_items.append(item)
            if args.limit and len(all_items) >= args.limit:
                break
        if len(page_items) < 10:
            break
        if total_available is not None and len(all_items) >= total_available:
            break

    return {
        "query": {
            "location": args.location,
            "resolved_location": coords.display_name,
            "lat": coords.lat,
            "lon": coords.lon,
            "radius_km": args.radius_km,
            "pages_requested": args.pages,
            "details": args.details,
        },
        "items": all_items,
        "returned": len(all_items),
        "total_available": total_available,
        "pages_seen": pages_seen,
        "runtime": {
            "approach": "browser-dom",
            "browser_session": args.browser_session,
            "proxy_used": bool(args.proxy),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract IFM practitioner listings as JSON.")
    parser.add_argument("--location", required=True, help='Search location, e.g. "Austin, TX".')
    parser.add_argument("--radius-km", type=int, default=40, help="Search radius in kilometers.")
    parser.add_argument("--pages", type=int, default=1, help="Number of result pages; 0 = until exhausted.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum practitioners to return; 0 = no explicit cap.")
    parser.add_argument("--details", action="store_true", help="Visit each full-detail page and enrich fields.")
    parser.add_argument("--lat", help="Skip geocoding and use this latitude.")
    parser.add_argument("--lon", help="Skip geocoding and use this longitude.")
    parser.add_argument("--browser-session", default=DEFAULT_SESSION, help="agent-browser session name.")
    parser.add_argument("--headed", action="store_true", help="Show browser; useful for first-run Cloudflare verification.")
    parser.add_argument("--proxy", default=os.getenv("RESIDENTIAL_PROXY_URL", ""), help="Proxy URL; defaults to RESIDENTIAL_PROXY_URL.")
    parser.add_argument(
        "--ignore-https-errors",
        action="store_true",
        default=os.getenv("IFM_IGNORE_HTTPS_ERRORS", "").lower() in {"1", "true", "yes"},
        help="Ignore browser TLS errors. Useful for BrightData SSL-inspection proxy unless its CA is installed in the browser profile.",
    )
    parser.add_argument("--reset-session", action="store_true", help="Close the named browser session before starting.")
    parser.add_argument("--wait-ms", type=int, default=5000, help="Wait after listing navigation.")
    parser.add_argument("--detail-wait-ms", type=int, default=2500, help="Wait after detail navigation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.radius_km < 1:
        raise ApiifyError("--radius-km must be >= 1")
    if args.pages < 0:
        raise ApiifyError("--pages must be >= 0")
    if args.limit < 0:
        raise ApiifyError("--limit must be >= 0")
    if bool(args.lat) != bool(args.lon):
        raise ApiifyError("--lat and --lon must be supplied together")
    print(json.dumps(run(args), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
