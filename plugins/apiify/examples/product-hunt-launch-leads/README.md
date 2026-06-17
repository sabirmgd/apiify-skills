# Product Hunt Launch Leads

This example turns Product Hunt launches into lead, partnership, and competitor-watch lists.

It uses Product Hunt's GraphQL API with a bearer token.

## Business Use

Track new launches by topic, capture maker/company metadata, and identify fresh teams that may need tooling, integrations, PR, design, recruiting, or sales support.

## Example

```bash
python3 apiified/product-hunt-launch-leads/script.py \
  --topic "ai" \
  --posted-after 2026-06-01 \
  --limit 25 \
  --output launches.json
```

## Output

- product_name
- tagline
- product_url
- website
- votes_count
- comments_count
- launch_date
- topics
- maker_names
- maker_profiles

## Known Risks

- Requires `PRODUCT_HUNT_TOKEN`.
- GraphQL query cost and rate limits apply.
- Product websites and maker profiles can be incomplete.
