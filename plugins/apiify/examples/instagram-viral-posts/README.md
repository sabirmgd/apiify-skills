# Instagram Viral Posts Extractor

This example documents a browser-login-then-HTTP artifact for pulling public hashtag media and ranking posts by engagement.

It is intentionally auth-aware: use a local browser session or cookie file, keep limits low, and never commit session cookies.

## Example

```bash
python3 apiified/instagram-viral-posts/script.py \
  --keyword "ai agents" \
  --limit 10 \
  --output instagram-posts.json
```

## Output

- post_url
- shortcode
- caption
- likes
- comments
- posted_date
- media_type
- media_url
- thumbnail
- username
- verified
- view_count
- engagement

## Known Risks

- Instagram web endpoints are undocumented and may change.
- Login may trigger checkpoints, rate limits, or account restrictions.
- Media URLs can expire and should not be used as durable storage links.
