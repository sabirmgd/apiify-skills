# RSS Feed Monitor

This example turns public RSS or Atom feeds into a structured monitoring feed.

It works for company blogs, press pages, industry publications, customer changelogs, and competitor content.

## Business Use

Track company announcements, funding posts, launches, pricing updates, and industry narratives without a news API key.

## Example

```bash
python3 apiified/rss-feed-monitor/script.py \
  --feed-url "https://www.ycombinator.com/blog/rss" \
  --limit 15 \
  --output feed-items.json
```

## Output

- feed_url
- title
- url
- source
- author
- published_at
- summary
- categories
- matched_keywords
- monitor_reason

## Known Risks

- RSS feeds vary in format and completeness.
- Some publishers truncate summaries.
- Feed use must respect each site's terms.
