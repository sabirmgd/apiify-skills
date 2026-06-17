# BuiltWith Technographic Leads

This example turns a target domain into technographic sales intelligence.

It uses BuiltWith's Domain API to identify technologies, categories, first-seen dates, and current usage signals.

## Business Use

Find accounts using a competitor, a complementary stack, or legacy technology that makes them a good outbound target.

## Example

```bash
python3 apiified/builtwith-technographic-leads/script.py \
  --domain "example.com" \
  --include-history \
  --output technographics.json
```

## Output

- domain
- technology
- category
- tag
- first_detected
- last_detected
- is_live
- vendor_url
- confidence
- spend_signal

## Known Risks

- Requires `BUILTWITH_API_KEY`.
- Technology detection can lag live site changes.
- Account scoring should combine this with firmographic and intent signals.
