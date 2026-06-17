# Runtime Tiers

Apiify should demote browser workflows into the lowest viable deterministic tier.

## Tier 1: Public API

Use official API docs, OpenAPI specs, SDKs, or documented exports.

Best for stability and user trust. Prefer this whenever it satisfies the output requirements.

## Tier 2: Private API Replay

Replay XHR, fetch, REST, or GraphQL calls discovered from the browser.

Capture:

- URL and method.
- Required headers.
- Request body/query params.
- Cookies/session model.
- Pagination cursors.
- Response schema.

Do not hardcode volatile tokens if they can be refreshed or read from a cookie/state file.

## Tier 3: Browser Login, HTTP Runtime

Use a real browser only to establish auth, then persist cookies/state and replay HTTP.

This is often the best tier for auth-gated consumer sites. It keeps the runtime cheap while still supporting login challenges.

## Tier 4: Browser DOM Runtime

Drive the browser and scrape rendered DOM.

Use only when:

- network responses are encrypted/opaque;
- all useful data is rendered only after client-side computation;
- anti-bot controls block HTTP replay;
- the user accepts fragility.

Mark as high drift risk.

