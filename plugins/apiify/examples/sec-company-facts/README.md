# SEC Company Facts

This example turns SEC public company facts into account and market signals without a third-party API key.

It uses SEC EDGAR data APIs with a descriptive user agent.

## Business Use

Track public-company revenue, segment, and filing metrics for account research, market sizing, and enterprise sales timing.

## Example

```bash
python3 apiified/sec-company-facts/script.py \
  --cik 0000320193 \
  --concept "us-gaap:Revenues" \
  --limit 20 \
  --output sec-facts.json
```

## Output

- cik
- entity_name
- taxonomy
- concept
- label
- unit
- fiscal_year
- fiscal_period
- form
- filed_at
- end_date
- value

## Known Risks

- SEC requires fair-access behavior and a descriptive user agent.
- Concepts vary by company and taxonomy.
- This covers public companies, not private SMB leads.
