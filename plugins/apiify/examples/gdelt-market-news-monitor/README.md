# GDELT Market News Monitor

This example turns global news coverage into market and geopolitical monitoring signals.

It uses GDELT's DOC API for public web news search.

## Business Use

Monitor market narratives, country risk, supply-chain events, competitor mentions, and regional demand signals without relying on one publisher.

## Example

```bash
python3 apiified/gdelt-market-news-monitor/script.py \
  --query "\"data centers\" \"Saudi Arabia\"" \
  --mode artlist \
  --max-records 50 \
  --output gdelt-news.json
```

## Output

- title
- url
- source_country
- domain
- language
- seen_at
- tone
- image_url
- social_image
- matched_query

## Known Risks

- GDELT search syntax and result ranking can change.
- Machine-translated or syndicated articles can duplicate stories.
- Tone and country fields are signals, not ground truth.
