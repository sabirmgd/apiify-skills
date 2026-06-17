# Meta Ad Library Monitor

This example turns Meta Ad Library searches into competitor advertising intelligence.

It uses Meta's Ad Library API where the user's access and geography support the requested ad type.

## Business Use

Track competitor creative, messaging, calls to action, landing pages, and active ad windows for marketing research.

## Example

```bash
python3 apiified/meta-ad-library-monitor/script.py \
  --query "acme crm" \
  --country US \
  --ad-type all \
  --limit 25 \
  --output meta-ads.json
```

## Output

- ad_archive_id
- page_name
- page_id
- ad_snapshot_url
- ad_delivery_start_time
- ad_delivery_stop_time
- ad_creative_bodies
- ad_creative_link_titles
- ad_creative_link_descriptions
- publisher_platforms

## Known Risks

- Requires Meta developer access and a valid token.
- Available ad types vary by country and policy rules.
- Creative fields and delivery data can be partial.
