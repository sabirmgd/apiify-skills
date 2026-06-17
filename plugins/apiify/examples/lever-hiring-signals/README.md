# Lever Hiring Signals

This example turns public Lever job boards into hiring-intent account signals without an API key.

It uses Lever's public postings API, not the authenticated Lever Data API.

## Business Use

Find accounts hiring for roles that imply new budget, pain, or tooling needs: RevOps, AI, security, support, sales, or data.

## Example

```bash
python3 apiified/lever-hiring-signals/script.py \
  --site "anchorage" \
  --team "Product" \
  --limit 20 \
  --output lever-jobs.json
```

## Output

- company_site
- job_id
- title
- team
- department
- location
- commitment
- hosted_url
- apply_url
- signal_tags

## Known Risks

- Only public Lever postings are covered.
- Site tokens must be discovered from a company's careers URL.
- Job text should be summarized before importing into a CRM.
