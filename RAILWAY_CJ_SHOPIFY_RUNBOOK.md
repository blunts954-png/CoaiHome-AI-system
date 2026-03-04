# Railway + Shopify + CJ Runbook (Production Path)

## 1) What was actually broken

1. OAuth installs were process-local only, so deploy/restart wiped authentication context.
2. Shopify client attempted a `client_credentials` flow that Shopify Admin API does not use for normal app installs.
3. No single deployment checklist tied Railway env vars, Shopify app settings, and CJ credentials together.

## 2) What is now implemented in code

- OAuth state and installation tokens are persisted in DB tables:
  - `shopify_oauth_states`
  - `shopify_installations`
- OAuth routes now write/read persisted state/install rows instead of in-memory dict caches.
- Shopify API client now uses:
  1. `SHOPIFY_ACCESS_TOKEN` when set, else
  2. persisted OAuth installation token.
- Added health endpoint: `GET /api/system/health`.

## 3) Railway deployment sequence

1. Provision PostgreSQL in Railway.
2. Set env vars from `.env.railway.example`.
3. Deploy the app and verify startup logs show DB init success.
4. Open:
   - `https://YOUR-RAILWAY-APP.up.railway.app/auth/shopify/install?shop=your-shop.myshopify.com`
5. Complete Shopify OAuth grant.
6. Validate install persistence:
   - `GET /auth/shopify/status?shop=your-shop.myshopify.com` should return `installed: true`
7. Validate runtime readiness:
   - `GET /api/system/health?shop=your-shop.myshopify.com`
8. Validate full diagnostics:
   - `python check_status.py`

## 4) CJ product pipeline flow

1. Ensure `CJ_API_TOKEN` is present.
2. Trigger product research:
   - `POST /api/research/run?store_id=1&niche=home%20organization`
3. Review queue:
   - `GET /api/products/pending`
4. Approve products:
   - `POST /api/products/{id}/approve`
5. Trigger sync to local DB:
   - `POST /api/system/sync-shopify`

## 5) Shipping / fulfillment operational flow

1. Fetch orders:
   - `GET /api/shopify/orders?status=any&limit=50`
2. Monitor exceptions:
   - `GET /api/exceptions`
3. Resolve exceptions manually when supplier issue appears:
   - `POST /api/exceptions/{id}/resolve`
4. Schedule automation loop from `automation/full_automation.py` after credentials are stable.

## 6) Remaining hardening (next sprint)

- Encrypt Shopify access tokens at rest.
- Add integration tests for OAuth callback and persisted install retrieval.
- Add webhook handlers for order-paid and fulfillment-updated events.
- Add dead-letter retry queue for CJ API failures.
