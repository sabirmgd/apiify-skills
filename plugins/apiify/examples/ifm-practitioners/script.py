#!/usr/bin/env python3
"""IFM practitioner directory extractor.

Runtime model:
  - IFM's listing/detail pages are public and server-render practitioner data.
  - This script tries direct HTTP with browser-like headers by default.
  - agent-browser remains available as a fallback for challenge cases.
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
from html import unescape
from urllib.parse import quote, quote_plus, urljoin

import requests


BASE = "https://www.ifm.org"
DEFAULT_SESSION = "ifm-practitioners-api"
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
CHALLENGE_RE = re.compile(r"Just a moment|security verification|Enable JavaScript and cookies", re.I)
HTML_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
}


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


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    without_tags = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    without_tags = re.sub(r"<style\b[^>]*>.*?</style>", " ", without_tags, flags=re.I | re.S)
    without_tags = re.sub(r"<svg\b[^>]*>.*?</svg>", " ", without_tags, flags=re.I | re.S)
    without_tags = re.sub(r"<[^>]+>", " ", without_tags)
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def first_match(pattern: str, text: str, flags: int = re.I | re.S) -> str | None:
    match = re.search(pattern, text, flags)
    return clean_text(match.group(1)) if match else None


def decode_cloudflare_email(encoded: str | None) -> str | None:
    if not encoded:
        return None
    try:
        key = int(encoded[:2], 16)
        return "".join(chr(int(encoded[i : i + 2], 16) ^ key) for i in range(2, len(encoded), 2))
    except ValueError:
        return None


def extract_cf_email(html: str) -> str | None:
    match = re.search(r"data-cfemail=[\"']([0-9a-f]+)[\"']", html, re.I)
    if match:
        return decode_cloudflare_email(match.group(1))
    match = re.search(r"/cdn-cgi/l/email-protection#([0-9a-f]+)", html, re.I)
    return decode_cloudflare_email(match.group(1)) if match else None


def absolute_url(href: str | None) -> str | None:
    return urljoin(BASE, href) if href else None


def extract_links(html: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for match in re.finditer(r"<a\b([^>]*)>(.*?)</a>", html, re.I | re.S):
        attrs, body = match.groups()
        href_match = re.search(r"href=[\"']([^\"']+)[\"']", attrs, re.I)
        if not href_match:
            continue
        href = unescape(href_match.group(1))
        links.append({"href": href, "absolute": absolute_url(href) or "", "text": clean_text(body)})
    return links


def is_external_site(link: dict[str, str]) -> bool:
    href = link["absolute"]
    return bool(
        re.match(r"^https?://", href, re.I)
        and not re.search(r"ifm\.org|google\.|maps\.google|cookiebot|sharethis", href, re.I)
    )


def extract_list_items(html: str) -> list[str]:
    return [
        item
        for item in (clean_text(match.group(1)) for match in re.finditer(r"<li\b[^>]*>(.*?)</li>", html, re.I | re.S))
        if item
    ]


def section_after_heading(html: str, heading_pattern: str) -> str:
    heading = re.search(
        rf"<h[23]\b[^>]*>.*?{heading_pattern}.*?</h[23]>",
        html,
        re.I | re.S,
    )
    if not heading:
        return ""
    rest = html[heading.end() :]
    next_heading = re.search(r"<h[23]\b", rest, re.I)
    return rest[: next_heading.start()] if next_heading else rest


def extract_section_list(html: str, heading_pattern: str) -> list[str]:
    return list(dict.fromkeys(extract_list_items(section_after_heading(html, heading_pattern))))


def build_http_session(args: argparse.Namespace) -> requests.Session:
    session = requests.Session()
    session.headers.update(HTML_HEADERS)
    if args.proxy:
        session.proxies.update({"http": args.proxy, "https": args.proxy})
    return session


def http_get(args: argparse.Namespace, session: requests.Session, url: str) -> str:
    log(f"GET {url}")
    last_error = "request did not run"
    for attempt in range(args.http_retries + 1):
        response = session.get(url, timeout=30, verify=not args.ignore_https_errors)
        challenged = response.headers.get("cf-mitigated") == "challenge" or CHALLENGE_RE.search(response.text)
        if response.status_code < 400 and not challenged:
            return response.text

        if challenged:
            last_error = "IFM returned a Cloudflare/security challenge to direct HTTP"
        else:
            snippet = clean_text(response.text[:500])
            last_error = f"HTTP {response.status_code} for {url}: {snippet}"

        if attempt < args.http_retries:
            time.sleep(args.http_retry_delay * (attempt + 1))

    raise ApiifyError(last_error)


def parse_listing_card(html: str) -> dict[str, Any]:
    name = first_match(r"<h3\b[^>]*class=[\"'][^\"']*\bname\b[^\"']*[\"'][^>]*>(.*?)</h3>", html)
    links = extract_links(html)
    detail_link = next((link for link in links if re.search(r"full details", link["text"], re.I)), None)
    email_link = next((link for link in links if link["href"].lower().startswith("mailto:")), None)
    phone_link = next((link for link in links if link["href"].lower().startswith("tel:")), None)
    schedule_link = next((link for link in links if re.search(r"schedule", link["text"], re.I)), None)
    website_link = next((link for link in links if is_external_site(link) and not re.search(r"schedule", link["text"], re.I)), None)
    distance_match = re.search(r"(\d+(?:\.\d+)?)\s+miles\s*/\s*(\d+(?:\.\d+)?)\s+km", clean_text(html), re.I)

    features_match = re.search(
        r"<ul\b[^>]*class=[\"'][^\"']*\bfeatured-highlight-list\b[^\"']*[\"'][^>]*>(.*?)</ul>",
        html,
        re.I | re.S,
    )
    features = extract_list_items(features_match.group(1) if features_match else "")

    description_match = re.search(
        r"<div\b[^>]*class=[\"'][^\"']*\bpractice-description\b[^\"']*[\"'][^>]*>(.*?)(?:<ul\b[^>]*class=[\"'][^\"']*\bfeatured-highlight-list\b|</div>)",
        html,
        re.I | re.S,
    )
    summary = clean_text(description_match.group(1))[:1200] if description_match else ""

    email = None
    if email_link:
        email = email_link["href"].replace("mailto:", "", 1).split("?", 1)[0]
    email = email or extract_cf_email(html)

    return {
        "name": name,
        "profile_url": detail_link["absolute"] if detail_link else None,
        "distance_miles": float(distance_match.group(1)) if distance_match else None,
        "distance_km": float(distance_match.group(2)) if distance_match else None,
        "phone": phone_link["href"].replace("tel:", "", 1) if phone_link else None,
        "email": email,
        "website": website_link["absolute"] if website_link else None,
        "schedule_url": schedule_link["absolute"] if schedule_link else None,
        "offers_telehealth": bool(re.search(r"Offers\s+Telehealth|OFFERS\s+TELEHEALTH", html, re.I)),
        "card_summary": summary or None,
        "card_features": features,
    }


def parse_listing_html(html: str, url: str) -> dict[str, Any]:
    cards = [
        part
        for part in re.split(r"(?=<li\b[^>]*class=[\"'][^\"']*\bpractitioner-card\b)", html, flags=re.I)
        if re.match(r"<li\b[^>]*class=[\"'][^\"']*\bpractitioner-card\b", part, re.I)
    ]
    items = [parse_listing_card(card) for card in cards]
    return {
        "url": url,
        "title": first_match(r"<title\b[^>]*>(.*?)</title>", html),
        "cloudflare_challenge": bool(CHALLENGE_RE.search(html)),
        "total_text": first_match(r"(\d+\s+practices found)", html),
        "items": [item for item in items if item.get("name")],
    }


def parse_detail_html(html: str, url: str) -> dict[str, Any]:
    links = extract_links(html)
    email_link = next((link for link in links if link["href"].lower().startswith("mailto:")), None)
    phone_link = next((link for link in links if link["href"].lower().startswith("tel:")), None)
    schedule_link = next((link for link in links if re.search(r"schedule", link["text"], re.I)), None)
    website_link = next((link for link in links if is_external_site(link) and not re.search(r"schedule", link["text"], re.I)), None)
    directions_link = next((link for link in links if re.search(r"directions", link["text"], re.I)), None)
    body_text = clean_text(html)

    email = None
    if email_link:
        email = email_link["href"].replace("mailto:", "", 1).split("?", 1)[0]
    email = email or extract_cf_email(html)

    telehealth_match = re.search(r"Available in\s+(.+?)(?:Call the Practitioner|Email the Practitioner|</div>)", body_text, re.I)
    language_block = section_after_heading(html, r"Languages Spoken")
    languages = [
        value
        for value in (
            clean_text(match.group(1))
            for match in re.finditer(r"<div\b[^>]*class=[\"'][^\"']*\blanguage-label\b[^\"']*[\"'][^>]*>(.*?)</div>", language_block, re.I | re.S)
        )
        if value
    ]

    return {
        "detail_url": url,
        "name": first_match(r"<h1\b[^>]*class=[\"'][^\"']*\bname\b[^\"']*[\"'][^>]*>(.*?)</h1>", html),
        "payment": first_match(r"<div\b[^>]*class=[\"'][^\"']*\binsurance\b[^\"']*[\"'][^>]*>.*?<div\b[^>]*class=[\"'][^\"']*\blabel\b[^\"']*[\"'][^>]*>(.*?)</div>", html),
        "profile_last_updated": first_match(r"Profile last updated\s+([0-9/]+)", body_text, flags=re.I),
        "phone": phone_link["href"].replace("tel:", "", 1) if phone_link else None,
        "email": email,
        "website": website_link["absolute"] if website_link else None,
        "schedule_url": schedule_link["absolute"] if schedule_link else None,
        "directions_url": directions_link["absolute"] if directions_link else None,
        "address": first_match(r"Address:\s*(.*?)\s+Phone:", body_text, flags=re.I),
        "fax": first_match(r"Fax:\s*(.*?)\s+Email:", body_text, flags=re.I),
        "offers_telehealth": bool(re.search(r"OFFERS TELEHEALTH|Telehealth Options", body_text, re.I)),
        "telehealth_locations": clean_text(telehealth_match.group(1)) if telehealth_match else None,
        "languages": list(dict.fromkeys(languages)),
        "health_concerns": extract_section_list(html, r"Health Concerns Addressed"),
        "coursework": extract_section_list(html, r"IFM Course Work"),
        "qualifications": extract_section_list(html, r"Graduate School Education"),
        "professional_associations": extract_section_list(html, r"Professional Associations"),
    }


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


def load_listing_http(args: argparse.Namespace, session: requests.Session, url: str) -> dict[str, Any]:
    html = http_get(args, session, url)
    result = parse_listing_html(html, url)
    if result.get("cloudflare_challenge"):
        raise ApiifyError("IFM returned a Cloudflare/security challenge to direct HTTP")
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


def enrich_detail_http(args: argparse.Namespace, session: requests.Session, item: dict[str, Any]) -> dict[str, Any]:
    profile_url = item.get("profile_url")
    if not profile_url:
        return item
    log(f"GET detail: {item.get('name')}")
    if args.request_delay:
        time.sleep(args.request_delay)
    html = http_get(args, session, profile_url)
    detail = parse_detail_html(html, profile_url)
    merged = dict(item)
    merged["detail"] = detail
    for key, value in detail.items():
        if value not in (None, "", [], {}) and not merged.get(key):
            merged[key] = value
    return merged


def parse_total(total_text: str | None) -> int | None:
    if not total_text:
        return None
    match = re.search(r"(\d+)", total_text)
    return int(match.group(1)) if match else None


def run_with_runtime(args: argparse.Namespace, *, runtime: str) -> dict[str, Any]:
    if runtime == "browser" and args.reset_session:
        try:
            run_agent_browser(args, ["close"])
        except ApiifyError:
            pass

    coords = Coordinates(args.lat, args.lon, args.location) if args.lat and args.lon else geocode(args.location)
    http_session = build_http_session(args) if runtime == "http" else None
    all_items: list[dict[str, Any]] = []
    total_available: int | None = None
    pages_seen: list[str] = []

    max_pages = args.pages if args.pages > 0 else 100
    for page_index in range(max_pages):
        if args.limit and len(all_items) >= args.limit:
            break
        url = build_listing_url(args.location, args.radius_km, page_index, coords)
        if runtime == "http" and page_index > 0 and args.request_delay:
            time.sleep(args.request_delay)
        if runtime == "http":
            assert http_session is not None
            listing = load_listing_http(args, http_session, url)
        else:
            listing = ensure_loaded(args, url, args.wait_ms)
        pages_seen.append(str(listing.get("url") or url))
        total_available = total_available or parse_total(listing.get("total_text"))
        page_items = listing.get("items") or []
        if not page_items:
            break
        for item in page_items:
            if args.details:
                if runtime == "http":
                    assert http_session is not None
                    item = enrich_detail_http(args, http_session, item)
                else:
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
            "mode": args.mode,
        },
        "items": all_items,
        "returned": len(all_items),
        "total_available": total_available,
        "pages_seen": pages_seen,
        "runtime": {
            "approach": "direct-http" if runtime == "http" else "browser-dom",
            "browser_session": args.browser_session if runtime == "browser" else None,
            "proxy_used": bool(args.proxy),
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode == "http":
        return run_with_runtime(args, runtime="http")
    if args.mode == "browser":
        return run_with_runtime(args, runtime="browser")
    try:
        return run_with_runtime(args, runtime="http")
    except ApiifyError as exc:
        log(f"Direct HTTP failed, falling back to browser: {exc}")
        return run_with_runtime(args, runtime="browser")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract IFM practitioner listings as JSON.")
    parser.add_argument("--location", required=True, help='Search location, e.g. "Austin, TX".')
    parser.add_argument("--radius-km", type=int, default=40, help="Search radius in kilometers.")
    parser.add_argument("--pages", type=int, default=1, help="Number of result pages; 0 = until exhausted.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum practitioners to return; 0 = no explicit cap.")
    parser.add_argument("--details", action="store_true", help="Visit each full-detail page and enrich fields.")
    parser.add_argument("--mode", choices=("auto", "http", "browser"), default="auto", help="Runtime mode. auto tries direct HTTP before browser fallback.")
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
    parser.add_argument("--http-retries", type=int, default=3, help="Retries for transient direct HTTP challenge/403 responses.")
    parser.add_argument("--http-retry-delay", type=float, default=3.0, help="Base sleep seconds between direct HTTP retries.")
    parser.add_argument("--request-delay", type=float, default=0.5, help="Sleep seconds between direct HTTP page/detail requests.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.radius_km < 1:
        raise ApiifyError("--radius-km must be >= 1")
    if args.pages < 0:
        raise ApiifyError("--pages must be >= 0")
    if args.limit < 0:
        raise ApiifyError("--limit must be >= 0")
    if args.http_retries < 0:
        raise ApiifyError("--http-retries must be >= 0")
    if args.http_retry_delay < 0:
        raise ApiifyError("--http-retry-delay must be >= 0")
    if args.request_delay < 0:
        raise ApiifyError("--request-delay must be >= 0")
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
