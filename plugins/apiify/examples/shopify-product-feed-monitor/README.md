# Shopify Product Feed Monitor

This example turns public Shopify product JSON feeds into competitor catalog and pricing intelligence.

Many Shopify storefronts expose a bounded `products.json` feed that can be discovered from the browser or guessed from the storefront domain.

## Business Use

Monitor product launches, pricing, variants, tags, inventory language, and merchandising changes for ecommerce competitors.

## Example

```bash
python3 apiified/shopify-product-feed-monitor/script.py \
  --store-url "https://www.allbirds.com" \
  --limit 25 \
  --output products.json
```

## Output

- store_url
- product_id
- title
- handle
- product_url
- vendor
- product_type
- tags
- published_at
- variant_count
- price_min
- price_max

## Known Risks

- Not every Shopify store exposes this feed.
- Product feeds can be disabled, cached, or rate limited.
- Respect storefront terms and keep request volume low.
