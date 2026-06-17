# IFM Practitioners Extractor

This example turns IFM's public practitioner directory into a direct HTTP JSON extractor.

IFM did not expose a stable public practitioner JSON API during discovery, but its practitioner listing and detail pages are server-rendered. The script uses browser-like HTTP headers, parses the public HTML directly, and falls back to `agent-browser` only when direct HTTP is challenged.

## Example

```bash
python3 apiified/ifm-practitioners/script.py \
  --mode http \
  --location "Austin, TX" \
  --radius-km 40 \
  --pages 1 \
  --limit 10
```

For detail enrichment:

```bash
python3 apiified/ifm-practitioners/script.py \
  --mode http \
  --location "Austin, TX" \
  --radius-km 40 \
  --pages 1 \
  --limit 1 \
  --details
```

For a larger detail run:

```bash
python3 apiified/ifm-practitioners/script.py \
  --mode http \
  --location "Austin, TX" \
  --radius-km 40 \
  --pages 10 \
  --limit 100 \
  --details \
  --request-delay 0.5 \
  --http-retries 3
```

For automatic browser fallback:

```bash
python3 apiified/ifm-practitioners/script.py \
  --mode auto \
  --location "Austin, TX" \
  --radius-km 40 \
  --pages 1 \
  --limit 10 \
  --browser-session ifm-detail
```

For residential proxy testing, keep credentials in the environment:

```bash
RESIDENTIAL_PROXY_URL="http://user:password@host:port" \
python3 apiified/ifm-practitioners/script.py \
  --mode auto \
  --location "Austin, TX" \
  --radius-km 40 \
  --limit 3 \
  --browser-session ifm-proxy-test \
  --reset-session \
  --ignore-https-errors
```

## Output

Base listings return:

- practitioner name
- IFM profile URL
- distance
- public email/phone/website links when present
- scheduling URL when present
- telehealth flag
- listing-card summary and features

`--details` opens each public IFM profile and can add:

- detail URL
- payment/profile update fields
- telehealth location text
- health concerns
- IFM coursework
- qualifications
- professional associations

## Runtime Notes

This is a Tier 2 public HTML artifact with browser fallback. Direct HTTP was verified for listings and detail pages, including Cloudflare email-protection decoding. Cookie-backed replay was not needed in testing; IFM cookies made the tested replay return Cloudflare challenges.

Cloudflare can still challenge direct HTTP intermittently. The script retries direct HTTP and `--mode auto` falls back to the browser runtime if direct access fails.

In verification, direct HTTP returned 10 listing rows in 4.72s and 3 detail-enriched rows in 14.62s. A 100-detail run should be measured in minutes, not the 15-25 minute browser-only estimate, but it can still slow down if Cloudflare returns transient challenges and retries kick in.
