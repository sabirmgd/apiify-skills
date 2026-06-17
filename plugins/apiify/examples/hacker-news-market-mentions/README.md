# Hacker News Market Mentions

This example turns Hacker News search into a no-key market signal feed.

It uses the public HN Algolia API.

## Business Use

Monitor founder discussions, product complaints, launch reactions, competitor mentions, and technical buyer pain.

## Example

```bash
python3 apiified/hacker-news-market-mentions/script.py \
  --query "ai agents" \
  --limit 20 \
  --output hn-mentions.json
```

## Output

- title
- url
- hn_url
- author
- points
- num_comments
- created_at
- tags
- market_signal
- excerpt

## Known Risks

- HN is a narrow technical audience.
- Search ranking is controlled by Algolia.
- This is public discussion intelligence, not direct contact enrichment.
