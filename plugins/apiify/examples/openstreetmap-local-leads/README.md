# OpenStreetMap Local Leads

This example turns a public place search into a local-business prospect list without a paid maps API key.

It uses Nominatim/OpenStreetMap search with a descriptive user agent and low request volume.

## Business Use

Build lightweight local lead lists by category and city, then enrich manually or through a separate permitted source.

## Example

```bash
python3 apiified/openstreetmap-local-leads/script.py \
  --query "dentist Austin Texas" \
  --limit 10 \
  --output local-leads.json
```

## Output

- name
- display_name
- category
- type
- latitude
- longitude
- address
- osm_type
- osm_id
- lead_source_url

## Known Risks

- Public Nominatim is for light usage only.
- It is not a replacement for Google Places/Yelp-style contact enrichment.
- Some rows have sparse category or address data.
