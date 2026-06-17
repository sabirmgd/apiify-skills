# Reddit Buyer Intent Monitor

This example turns Reddit searches into buyer-intent and pain-point signals for sales and marketing teams.

It should use Reddit's authenticated API path rather than scraping pages.

## Business Use

Find posts where users ask for recommendations, complain about tools, compare vendors, or describe urgent pain in target communities.

## Example

```bash
python3 apiified/reddit-buyer-intent-monitor/script.py \
  --subreddit "salesops" \
  --query "recommend CRM automation" \
  --limit 25 \
  --output reddit-intent.json
```

## Output

- post_id
- subreddit
- title
- post_url
- author
- score
- num_comments
- created_at
- intent_label
- matched_keywords
- excerpt

## Known Risks

- Requires Reddit API access and a descriptive user agent.
- Respect subreddit rules and platform terms.
- Usernames and excerpts may be personal data; redact or minimize before sharing.
