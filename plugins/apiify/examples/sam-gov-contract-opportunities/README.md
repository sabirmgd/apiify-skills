# SAM.gov Contract Opportunities

This example turns government contract opportunities into B2G sales and partnership leads.

It uses the SAM.gov Get Opportunities Public API.

## Business Use

Monitor active solicitations by keyword, NAICS, agency, set-aside type, or date range, then export opportunities for bid/no-bid review.

## Example

```bash
python3 apiified/sam-gov-contract-opportunities/script.py \
  --keyword "cybersecurity" \
  --posted-from 06/01/2026 \
  --posted-to 06/17/2026 \
  --limit 25 \
  --output opportunities.json
```

## Output

- notice_id
- title
- solicitation_number
- agency
- office
- naics_code
- set_aside
- response_deadline
- posted_date
- opportunity_url

## Known Risks

- Requires a SAM.gov API key for practical usage.
- Date formats and filters must match SAM.gov expectations.
- Opportunity details can change after publication.
