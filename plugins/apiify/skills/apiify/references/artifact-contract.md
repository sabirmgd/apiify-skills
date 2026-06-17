# Artifact Contract

Every generated API artifact must be a small, inspectable folder.

## Required Files

```text
apiified/<slug>/
  script.py
  metadata.json
  README.md
  sample-output.redacted.json
```

## script.py

Requirements:

- CLI entrypoint with `argparse`.
- `--help` works.
- JSON is printed to stdout by default.
- Optional `--output <path>` writes JSON.
- No credentials or tokens are hardcoded.
- Secrets are read from env vars, local state files, or an explicit cookie/state path.
- HTTP errors include URL/status context but not secret headers.

Recommended flags:

- `--query`, `--url`, `--limit`, `--pages`, or domain-specific inputs.
- `--output` for JSON output.
- `--csv-output` when native CSV export is implemented.
- `--login` or `--headed` only when browser auth is needed.

## metadata.json

Required fields:

```json
{
  "name": "slug",
  "source": "https://example.com",
  "approach": "browser-login-then-http",
  "runtime_tier": 2,
  "description": "What the script extracts.",
  "inputs": [],
  "outputs": [],
  "auth": {},
  "verification_command": "python3 apiified/slug/script.py --query demo --limit 5",
  "verification_result": "5 items returned with required fields",
  "known_risks": []
}
```

Runtime tiers:

- `1`: public documented API.
- `2`: private XHR/GraphQL/API replay.
- `3`: in-browser fetch or browser-login-then-HTTP.
- `4`: DOM scrape/browser replay.

## README.md

Include:

- What it extracts.
- Auth setup.
- Example commands.
- Output field list.
- Known risks.

## sample-output.redacted.json

Include a successful output shape with realistic fields, but redact secrets, private identifiers, and personal data where needed.

