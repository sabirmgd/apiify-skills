# Greenhouse Hiring Signals

This example turns public Greenhouse job boards into hiring-intent account signals.

It uses Greenhouse's Job Board API for published jobs.

## Business Use

Find companies hiring for target roles, infer budget or growth areas, and create account triggers for sales, recruiting, or partnership workflows.

## Example

```bash
python3 apiified/greenhouse-hiring-signals/script.py \
  --board-token "example-company" \
  --department "Engineering" \
  --limit 50 \
  --output jobs.json
```

## Output

- company
- board_token
- job_id
- title
- department
- location
- absolute_url
- updated_at
- content_summary
- signal_tags

## Known Risks

- Only companies using public Greenhouse boards are covered.
- Board token discovery may require a one-time browser lookup.
- Job descriptions can be long and should be summarized locally before CRM import.
