# Apiify Skills

Apiify is an agent skill/plugin for turning websites into callable APIs. It guides Claude Code or Codex through API discovery, browser-assisted capture, deterministic script generation, verification, and JSON/CSV export.

The core product idea is simple: pay the browser/LLM cost once during discovery, then run a deterministic script forever.

## What It Produces

Each run should create an artifact folder like:

```text
apiified/<slug>/
  script.py
  metadata.json
  README.md
  sample-output.redacted.json
  output.csv
```

The generated script should prefer direct HTTP replay. Browser automation is used for login, discovery, and last-resort DOM extraction.

## Install For Claude Code

From Claude Code:

```text
/plugin marketplace add sabirmgd/apiify-skills
/plugin install apiify@apiify
/reload-plugins
```

Then invoke:

```text
/apiify:apiify instagram viral posts for keyword "ai agents", output JSON and CSV
```

For local development before publishing:

```text
/plugin marketplace add .
/plugin install apiify@apiify
/reload-plugins
```

## Install For Codex

From a shell:

```bash
codex plugin marketplace add sabirmgd/apiify-skills
codex plugin add apiify@apiify
codex
```

Start a new thread, then invoke:

```text
Use $apiify:apiify to apiify Instagram viral posts for keyword "ai agents" with JSON and CSV output.
```

For local development:

```bash
codex plugin marketplace add .
codex plugin add apiify@apiify
codex
```

## Runtime Dependencies

The skill is designed to install/check its own local dependencies through scripts:

```bash
python3 plugins/apiify/skills/apiify/scripts/bootstrap.py --user
python3 plugins/apiify/skills/apiify/scripts/doctor.py
```

Bootstrap installs:

- `agent-browser` for browser discovery and logged-in flows.
- Chrome for Testing via `agent-browser install`.
- Python packages used by generated scripts: `requests` and `python-dotenv`.

## Skill Workflow

1. Clarify the task: target site, input parameters, output fields, auth method, limit, and verification query.
2. Research public/official APIs first.
3. If needed, use browser discovery with `agent-browser`: snapshot, interact, inspect network requests, save cookies/state.
4. Promote the workflow to the cheapest deterministic tier:
   - public API
   - private XHR/GraphQL replay
   - in-browser fetch with session cookies
   - DOM scrape as last resort
5. Generate a readable `script.py`, `metadata.json`, and usage docs.
6. Verify with a real run and export JSON/CSV.

## Safety

Apiify is for data and accounts the user is authorized to access. Do not paste real passwords into chat or shell history. Prefer headed login, browser state files, `.env` files, or one-time throwaway credentials. Redact cookies, bearer tokens, passwords, and account identifiers from committed examples.

Private web APIs are undocumented and may violate site terms or break without notice. Each generated artifact must record the endpoint tier, auth model, rate-limit risk, and known drift risk.

## Repository Layout

```text
.claude-plugin/marketplace.json       # Claude Code marketplace catalog
.agents/plugins/marketplace.json      # Codex marketplace catalog
plugins/apiify/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/apiify/
    SKILL.md
    agents/openai.yaml
    scripts/
    references/
  examples/
```
