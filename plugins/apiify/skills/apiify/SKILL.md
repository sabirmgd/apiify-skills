---
name: apiify
description: Turn a website, logged-in workflow, search page, feed, or browser task into a deterministic API script with JSON/CSV outputs. Use when the user asks to apiify/appify a site, reverse engineer web APIs, capture browser network calls, create reusable scrapers, or package a browser workflow as a callable endpoint/script.
allowed-tools: Bash(python3 *), Bash(python *), Bash(npm *), Bash(npx *), Bash(agent-browser *), Bash(curl *), Read, Write, Edit
---

# Apiify

You are converting a website workflow into a durable API artifact. The product is not a browser recording. The product is a readable, deterministic script plus metadata and verified output.

## First Run

Before discovery, check dependencies from this skill directory:

```bash
python3 scripts/doctor.py
```

If dependencies are missing and the user has asked for implementation, install them:

```bash
python3 scripts/bootstrap.py --user
python3 scripts/doctor.py
```

Do not paste user passwords, cookies, bearer tokens, or session IDs into chat or command history. Prefer headed browser login, browser state files, local `.env` files, or one-time throwaway credentials.

The standard public harness is `agent-browser@0.15.1`, installed by `scripts/bootstrap.py` and verified by `scripts/doctor.py`. Do not assume ActionHub, ahbrowser, Patchright, or Playwright are already present on the user's machine. If a generated artifact needs a browser, use the packaged harness unless the artifact explicitly owns and documents another dependency.

## Required Clarifications

For each target, lock these before building:

- Source: exact website/page/search/feed/workflow.
- Inputs: query, URL, account, date range, limit, pagination, sort.
- Outputs: exact fields and formats. Default to JSON plus CSV.
- Auth: public, browser login once, env credentials, token, or user-supplied cookie file.
- Verification: one real query/run and expected minimum result count.

Keep questions minimal. If a reasonable default exists, choose it and continue.

## Runtime Tiers

Always climb down toward cheaper deterministic execution:

1. Public documented API.
2. Private XHR/GraphQL/API replay with cookies/headers.
3. In-browser fetch using authenticated session state.
4. Browser DOM scrape.

Tier 4 is acceptable only when lower tiers fail. Mark it as drift-prone in metadata.

## Browser Harness

Use `agent-browser` as the portable browser harness:

```bash
agent-browser --session "<slug>" open "<url>"
agent-browser --session "<slug>" snapshot -i --compact
agent-browser --session "<slug>" network requests --filter "api|json|graphql|search|feed|posts|data"
agent-browser --session "<slug>" cookies get
agent-browser --session "<slug>" screenshot "/tmp/<slug>.png"
agent-browser --session "<slug>" close
```

Use browser discovery to answer two questions:

- What interactable controls does the user workflow require?
- Which network calls can replace the browser at runtime?

If the browser route is needed for login, save/reuse browser state or cookies. The final script should still prefer HTTP replay after login.

## API Research Rules

Research the cheapest path first:

- Search for official API/docs/OpenAPI schemas.
- Inspect HTML for embedded state, config, app IDs, GraphQL operation names, and API base URLs.
- Capture real browser network traffic only after public API research is insufficient.
- Preserve exact headers and request payloads needed for replay, but redact secrets.

Do not overfit to one successful response. Verify pagination, auth expiry, empty results, rate limits, and changed query terms when feasible.

## Artifact Contract

Create artifacts under:

```text
apiified/<slug>/
  script.py
  metadata.json
  README.md
  sample-output.redacted.json
```

The script must:

- expose `--help`;
- accept explicit inputs instead of hardcoded query strings;
- print JSON to stdout by default;
- support `--output <path>` for JSON when useful;
- support CSV either natively or through `scripts/export_csv.py`;
- fail loudly with actionable errors;
- avoid logging secrets.

Validate metadata with:

```bash
python3 scripts/metadata_schema.py apiified/<slug>/metadata.json
```

Export CSV from JSON with:

```bash
python3 scripts/export_csv.py apiified/<slug>/output.json --output apiified/<slug>/output.csv
```

See `references/artifact-contract.md`.

## Metadata Requirements

`metadata.json` must include:

- `name`
- `source`
- `approach`
- `runtime_tier`
- `description`
- `inputs`
- `outputs`
- `auth`
- `verification_command`
- `verification_result`
- `known_risks`

For private APIs, include endpoint paths but redact tokens/cookies.

## Verification

Before reporting done:

1. Run `python3 -m py_compile apiified/<slug>/script.py`.
2. Run `python3 apiified/<slug>/script.py --help`.
3. Run the real verification command.
4. Save a redacted sample output.
5. Validate metadata.
6. Export CSV if requested or if the output is tabular.

Report the exact files changed, the command that proved it worked, and remaining risks.

## Quality Bar

Good Apiify output is:

- deterministic after discovery;
- readable enough for a developer to patch;
- explicit about auth and drift risks;
- tested with one real query;
- reusable by Claude Code, Codex, or a human shell.

Bad output is:

- a prompt-only browser macro;
- a script that requires the original agent session to run;
- a script with credentials in source;
- unverified code that only compiles;
- metadata that hides the runtime tier or risk.
