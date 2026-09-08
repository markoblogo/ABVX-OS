# Authenticated KDP portfolio audit

Book Radar may inspect the owner's already-authenticated KDP session in Safari when the owner authorizes the audit. This is a read-only evidence channel, not a publishing channel.

## Audit contract

1. Read Bookshelf status, formats, prices, ASINs, submission dates, and visible warnings.
2. Read Orders, KENP, and royalties for a stated period. Prefer 90 days for portfolio comparisons and a shorter launch window for new titles.
3. Keep availability, discovery, conversion, product fit, and observation time separate. Orders without impressions do not prove a conversion problem; zero orders on a title live for only a few days do not prove product-market failure.
4. Store an observed snapshot and source timestamp before recommending metadata, description, price, format, or packaging changes.
5. Never edit metadata, pricing, files, ads, enrollment, or publication status during an audit. Any KDP write needs a separate explicit instruction and the relevant human gate.

## Repeatability

The audit can be rerun on demand or weekly while Safari has a valid authenticated KDP session. If the session is unavailable or expired, record `AUTHENTICATED_CHANNEL_UNAVAILABLE`; do not infer account state from public search alone.

Minimum stored fields: `observed_at`, `period`, `title`, `format`, `status`, `price`, `asin`, `submitted_at`, `processed_units`, `kenp_pages` where applicable, `availability_confidence`, and `missing_denominators`.
