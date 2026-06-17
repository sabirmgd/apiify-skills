# IFM Practitioners Extractor

This example turns IFM's public practitioner directory into a browser-backed JSON extractor.

IFM did not expose a stable public practitioner JSON API during discovery. Direct HTTP requests returned Cloudflare challenge responses, so this artifact uses `agent-browser` against public listing and detail pages.

## Example

```bash
python3 apiified/ifm-practitioners/script.py \
  --location "Austin, TX" \
  --radius-km 40 \
  --pages 1 \
  --limit 10 \
  --browser-session ifm-detail
```

For detail enrichment:

```bash
python3 apiified/ifm-practitioners/script.py \
  --location "Austin, TX" \
  --radius-km 40 \
  --pages 1 \
  --limit 1 \
  --details \
  --browser-session ifm-detail
```

For residential proxy testing:

```bash
RESIDENTIAL_PROXY_URL="http://user:password@host:port" \
python3 apiified/ifm-practitioners/script.py \
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

This is a Tier 4 browser DOM artifact. A warmed browser session works, but a fresh residential-proxy browser session still hit Cloudflare in testing. Treat this as a reusable extractor with persistent session support, not as a guaranteed stateless HTTP scraper.
