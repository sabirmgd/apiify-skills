# Google Places Local Leads

This example turns local business searches into prospect lists for agencies, field sales teams, recruiters, and service providers.

It uses Google Places Text Search and Place Details. The script should keep fields explicit to control API cost.

## Business Use

Find businesses matching a service category and geography, then export rows for CRM import or enrichment.

## Example

```bash
python3 apiified/google-places-local-leads/script.py \
  --query "dental clinics in Austin" \
  --limit 25 \
  --output local-leads.json
```

## Output

- name
- place_id
- website
- phone
- address
- rating
- review_count
- business_status
- latitude
- longitude
- types

## Known Risks

- Requires a Google Maps Platform API key and billable Places requests.
- Place Details should request only needed fields.
- Some businesses lack website or phone fields.
