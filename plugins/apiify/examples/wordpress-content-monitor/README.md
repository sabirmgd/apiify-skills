# WordPress Content Monitor

This example turns public WordPress REST posts into competitor content intelligence.

It uses the built-in WordPress REST API exposed by many WordPress sites.

## Business Use

Track competitor blog cadence, topics, messaging, product education, security posts, and campaign themes.

## Example

```bash
python3 apiified/wordpress-content-monitor/script.py \
  --site-url "https://wordpress.org/news" \
  --limit 10 \
  --output wordpress-posts.json
```

## Output

- site_url
- post_id
- title
- url
- published_at
- modified_at
- author
- excerpt
- categories
- tags
- monitor_reason

## Known Risks

- Some WordPress sites disable or restrict REST endpoints.
- Category/tag names often require additional endpoint lookups.
- HTML excerpts should be sanitized before downstream use.
