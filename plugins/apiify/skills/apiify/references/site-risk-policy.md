# Site Risk Policy

Apiify must be used only for sites, accounts, and data the user is authorized to access.

## Public Skill Defaults

- Prefer documented APIs.
- Respect rate limits.
- Keep request volume bounded.
- Do not bypass paywalls, access controls, CAPTCHAs, or account restrictions.
- Do not build credential stuffing, spam, mass account creation, or scraping that targets private personal data.
- Record known terms/rate-limit/drift risks in metadata.

## Auth-Gated Sites

For consumer platforms with private web APIs:

- use a throwaway account when possible;
- keep limits small by default;
- make follower/profile enrichment opt-in if it causes per-author fanout;
- warn that endpoints are undocumented and may break;
- do not publish real cookies, tokens, or scraped private content in examples.

