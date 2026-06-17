# Sitemap Content Inventory

This example turns a public sitemap into a structured content and SEO inventory.

It follows the standard XML sitemap protocol.

## Business Use

Map competitor content, landing pages, product pages, docs, and launch pages without crawling the whole website.

## Example

```bash
python3 apiified/sitemap-content-inventory/script.py \
  --sitemap-url "https://www.shopify.com/sitemap.xml" \
  --limit 100 \
  --output sitemap-pages.json
```

## Output

- sitemap_url
- url
- last_modified
- change_frequency
- priority
- path
- section
- inferred_page_type
- monitor_reason

## Known Risks

- Sitemaps are hints, not guaranteed complete inventories.
- Large sitemap indexes require recursive fetching with caps.
- Robots and crawl policies still apply.
