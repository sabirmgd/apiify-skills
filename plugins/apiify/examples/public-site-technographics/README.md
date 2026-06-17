# Public Site Technographics

This example turns a company website into a lightweight technology signal without BuiltWith or Wappalyzer API keys.

It inspects public HTML, response headers, script URLs, meta tags, and common platform fingerprints.

## Business Use

Qualify accounts by visible stack signals: ecommerce platform, analytics tools, marketing pixels, CMS, support widgets, or legacy scripts.

## Example

```bash
python3 apiified/public-site-technographics/script.py \
  --url "https://www.shopify.com" \
  --output technographics.json
```

## Output

- url
- final_url
- status_code
- detected_technology
- category
- evidence
- confidence
- source
- first_party
- signal_for

## Known Risks

- This is lighter than commercial technographic databases.
- Hidden server-side systems cannot be detected from public HTML.
- Fingerprints need maintenance as vendors change script URLs.
