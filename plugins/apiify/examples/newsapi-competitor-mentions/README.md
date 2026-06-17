# NewsAPI Competitor Mentions

This example turns news search into a competitor, customer, and market-monitoring feed.

It uses NewsAPI's Everything endpoint.

## Business Use

Track brand mentions, competitor launches, funding news, executive changes, outages, regulatory changes, or industry narratives.

## Example

```bash
python3 apiified/newsapi-competitor-mentions/script.py \
  --query "\"Acme CRM\" OR \"Acme AI\"" \
  --from-date 2026-06-01 \
  --sort-by publishedAt \
  --limit 50 \
  --output news-mentions.json
```

## Output

- title
- source
- author
- url
- published_at
- description
- content_excerpt
- matched_query
- sentiment_hint

## Known Risks

- Requires `NEWSAPI_KEY`.
- Coverage and historical access depend on plan limits.
- Full article text usually requires publisher access and should not be scraped blindly.
