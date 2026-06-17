# Apiify Skills

Apiify is an agent skill/plugin for turning websites into callable APIs. It guides Claude Code or Codex through API discovery, browser-assisted capture, deterministic script generation, verification, and JSON/CSV export.

The core product idea is simple: pay the browser/LLM cost once during discovery, then run a deterministic script forever.

## Why This Exists

Agents are much better when they can call tools than when they have to manually drive browsers.

Browser work is useful for discovery, login, and messy workflows, but it is a bad runtime primitive:

- it is slow and expensive;
- it breaks when UI text or layout changes;
- it burns context on screenshots, DOM, and retries;
- it repeats the same exploration every time;
- it is hard to compose into larger agent workflows.

APIs are the opposite: structured, cheap, callable, testable, and easy for agents to chain. The problem is that many useful websites either do not expose a public API, hide their data behind private browser calls, or require enough technical work that non-technical users cannot turn the workflow into a tool.

Apiify bridges that gap. It helps an agent ask the right questions, research the public/private API surface, use a browser only when needed, and produce a script that another agent can call like a normal API.

## The Agent Workflow Shift

Without Apiify:

```text
agent -> open browser -> login -> click/search/filter -> scrape page -> retry on failure
```

With Apiify:

```text
one-time discovery -> generated script/API -> agent calls the script directly
```

That matters because once a workflow is converted into a deterministic script, it becomes a reusable capability. Any agent can call it, schedule it, combine it with other tools, export it to CSV, or wrap it as an endpoint.

## Use Cases

Apiify is useful when a person can get the data or complete the workflow in a browser, but there is no clean API available to the agent.

Common examples:

- **Lead generation:** build local business lists, startup lists, hiring-signal feeds, public-company account profiles, or ecommerce catalog monitors.
- **Sales triggers:** watch public job boards, RSS feeds, sitemaps, product feeds, and market discussions for new pain or budget signals.
- **Marketing intelligence:** monitor competitor content, launch reactions, product pages, pricing pages, and visible website stack signals.
- **News and market monitoring:** turn public RSS feeds, public search APIs, and public content feeds into structured alert rows.
- **Logged-in sales/admin portals:** convert repeatable CRM, analytics, marketplace, or dashboard workflows into scripts agents can call.
- **Prototype integrations before official API access:** reverse engineer enough of the browser flow to validate a product idea or automation before building a full integration.
- **Reduce agent runtime cost:** replace repeated browser navigation with a cheap deterministic HTTP call or script execution.

Example prompts:

```text
/apiify:apiify turn this real estate search page into a JSON/CSV extractor for price, address, agent, and listing URL.
```

```text
Use $apiify:apiify to convert this logged-in analytics dashboard export into a reusable script. Browser login once, then replay the underlying API if possible.
```

```text
/apiify:apiify find the API behind this product search page and generate a script that accepts --query and --limit.
```

Business-focused no-key example catalog:

| Example | Business job | Typical source |
| --- | --- | --- |
| `openstreetmap-local-leads` | Local business prospect lists | Nominatim/OpenStreetMap |
| `public-site-technographics` | Visible stack/account scoring | Public HTML + headers |
| `hacker-news-market-mentions` | Founder/technical market signals | HN Algolia search |
| `rss-feed-monitor` | Company blog, press, and industry monitoring | Public RSS/Atom feeds |
| `lever-hiring-signals` | Hiring intent and growth triggers | Lever public postings |
| `greenhouse-hiring-signals` | Hiring intent and growth triggers | Greenhouse Job Board API |
| `sec-company-facts` | Public-company account research | SEC EDGAR data APIs |
| `shopify-product-feed-monitor` | Ecommerce competitor catalog/pricing | Public storefront product feeds |
| `wordpress-content-monitor` | Competitor blog/content monitoring | WordPress REST posts |
| `sitemap-content-inventory` | Competitor SEO/content inventory | Public XML sitemaps |

The catalog validator rejects examples that require API keys, bearer tokens, or OAuth credentials. For live source checks, run:

```bash
python3 plugins/apiify/skills/apiify/scripts/smoke_no_key_examples.py
```

See `plugins/apiify/examples/yc-company-leads/` for a real directory-to-lead-list example. It turns YC's public company directory into a JSON/CSV extractor by discovering the underlying Algolia search API, with optional public profile enrichment for founder/social fields.

## When Not To Use It

Do not use Apiify to bypass access controls, paywalls, CAPTCHAs, account restrictions, or site rules. Prefer official APIs whenever they meet the need. For sensitive or high-volume use cases, review the target site's terms, rate limits, and privacy constraints first.

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
codex plugin list --available --json
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
codex plugin list --available --json
codex
```

## Runtime Dependencies

The skill is designed to install/check its own local dependencies through scripts:

```bash
python3 plugins/apiify/skills/apiify/scripts/bootstrap.py --user
python3 plugins/apiify/skills/apiify/scripts/doctor.py
```

Bootstrap installs:

- `agent-browser@0.15.1` for browser discovery and logged-in flows.
- Chrome for Testing via `agent-browser install`.
- Python packages used by generated scripts: `requests` and `python-dotenv`.

`doctor.py` verifies the same pinned `agent-browser` version. If a user has a different version installed, it fails and tells them to rerun bootstrap. You can override the pin deliberately with:

```bash
APIIFY_AGENT_BROWSER_VERSION=0.15.1 python3 plugins/apiify/skills/apiify/scripts/bootstrap.py --user
```

### Harness Model

Apiify packages the harness as deterministic scripts plus a pinned browser CLI dependency. It does not expect every user to already have the same local setup.

The standard public harness is:

```text
Apiify skill -> bootstrap.py -> agent-browser@0.15.1 -> Chrome for Testing
```

Older internal experiments used ActionHub/ahbrowser and Patchright directly. This public package does not depend on ActionHub or a local Patchright install. That is intentional: users should get one portable harness from the package, not whatever happens to be on the author's machine.

Generated artifacts should still try to escape the browser at runtime:

```text
public API -> private XHR/GraphQL replay -> browser-login-then-HTTP -> DOM scrape
```

Browser automation is the discovery/login tool. The final output should be a script/API that agents can call cheaply.

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
