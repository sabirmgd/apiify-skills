# Hunter Domain Contacts

This example turns a company domain into sales contact candidates for outbound workflows.

It uses Hunter's Domain Search API and should only be used for lawful B2B prospecting that respects unsubscribe, consent, and data-protection rules.

## Business Use

Enrich target accounts with likely departments, public sources, confidence, and verification state before handing leads to a sales workflow.

## Example

```bash
python3 apiified/hunter-domain-contacts/script.py \
  --domain "example.com" \
  --department sales \
  --limit 20 \
  --output contacts.json
```

## Output

- domain
- organization
- first_name
- last_name
- position
- department
- email
- confidence
- verification_status
- sources_count

## Known Risks

- Requires `HUNTER_API_KEY`.
- Contact data must be handled under applicable privacy and outreach laws.
- Returned contacts are candidates, not guaranteed buyers.
