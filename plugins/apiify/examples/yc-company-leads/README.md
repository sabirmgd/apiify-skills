# YC Company Leads Extractor

This is a concrete Apiify test for the "directory to lead list" use case.

The YC company directory looks like a browser/search workflow, but the page uses a public Algolia index. Apiify discovers that once and turns it into a deterministic script.

## Example

```bash
python3 apiified/yc-company-leads/script.py \
  --query "ai agents" \
  --limit 25 \
  --enrich \
  --output /tmp/yc-leads.json \
  --csv-output /tmp/yc-leads.csv
```

## Output

Base search returns company-level fields:

- name
- website
- YC profile URL
- one-liner and long description
- batch
- industry/subindustry
- regions/locations
- tags
- team size
- hiring/top-company flags

`--enrich` fetches each public YC company profile and adds:

- company LinkedIn/Twitter/GitHub links when present
- year founded
- founder names/titles/social profile links when present

This demo intentionally does not scrape private emails, phone numbers, or gated data.

