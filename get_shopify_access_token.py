"""
Shopify OAuth helper for Dev Dashboard apps.

Generates the OAuth install URL and exchanges the returned `code` for an
Admin API access token. Credentials are loaded from `.env`.
"""
import argparse
import asyncio
import os
import re
import secrets
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

DEFAULT_SCOPES = (
    "read_products,write_products,read_orders,write_orders,"
    "read_inventory,write_inventory,read_customers"
)


def _normalize_shop(shop: str) -> str:
    if not shop:
        return ""
    shop = shop.strip().lower()
    shop = shop.replace("https://", "").replace("http://", "").strip("/")
    return shop


def _valid_shop(shop: str) -> bool:
    return bool(re.match(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$", shop))


def _require(name: str, value: str):
    if not value:
        raise ValueError(f"Missing {name}")


def _load_config(args: argparse.Namespace) -> dict:
    load_dotenv(override=True)

    shop = _normalize_shop(args.shop or os.getenv("SHOPIFY_SHOP_URL", ""))
    api_key = (os.getenv("SHOPIFY_API_KEY", "") or "").strip()
    api_secret = (os.getenv("SHOPIFY_API_SECRET", "") or "").strip()
    app_url = (args.app_url or os.getenv("SHOPIFY_APP_URL", "") or "").strip().rstrip("/")
    redirect_uri = (args.redirect_uri or "").strip()
    if not redirect_uri and app_url:
        redirect_uri = f"{app_url}/auth/shopify/callback"

    scopes = (args.scopes or os.getenv("SHOPIFY_API_SCOPES", "") or DEFAULT_SCOPES).strip()
    api_version = (os.getenv("SHOPIFY_API_VERSION", "2024-01") or "2024-01").strip()

    return {
        "shop": shop,
        "api_key": api_key,
        "api_secret": api_secret,
        "app_url": app_url,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "api_version": api_version,
    }


def _build_install_url(config: dict) -> tuple[str, str]:
    _require("SHOPIFY_SHOP_URL", config["shop"])
    _require("SHOPIFY_API_KEY", config["api_key"])
    _require("SHOPIFY_APP_URL or --redirect-uri", config["redirect_uri"])
    if not _valid_shop(config["shop"]):
        raise ValueError("Invalid shop domain. Use format: store-name.myshopify.com")

    state = secrets.token_urlsafe(24)
    query = urlencode(
        {
            "client_id": config["api_key"],
            "scope": config["scopes"],
            "redirect_uri": config["redirect_uri"],
            "state": state,
        }
    )
    return f"https://{config['shop']}/admin/oauth/authorize?{query}", state


async def _exchange_code(config: dict, code: str) -> str:
    _require("SHOPIFY_SHOP_URL", config["shop"])
    _require("SHOPIFY_API_KEY", config["api_key"])
    _require("SHOPIFY_API_SECRET", config["api_secret"])
    if not _valid_shop(config["shop"]):
        raise ValueError("Invalid shop domain. Use format: store-name.myshopify.com")

    token_url = f"https://{config['shop']}/admin/oauth/access_token"
    payload = {
        "client_id": config["api_key"],
        "client_secret": config["api_secret"],
        "code": code,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(token_url, json=payload)

    if response.status_code >= 400:
        raise RuntimeError(f"Token exchange failed ({response.status_code}): {response.text}")

    token = response.json().get("access_token", "")
    if not token:
        raise RuntimeError("Token exchange failed: missing access_token")
    return token


async def _test_token(shop: str, token: str, api_version: str) -> bool:
    url = f"https://{shop}/admin/api/{api_version}/shop.json"
    headers = {"X-Shopify-Access-Token": token}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
    return response.status_code == 200


def _upsert_env(path: str, key: str, value: str):
    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated = False
    for idx, line in enumerate(lines):
        if line.startswith(f"{key}=") or line.startswith(f"#{key}="):
            lines[idx] = f"{key}={value}\n"
            updated = True
            break

    if not updated:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(f"{key}={value}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser(description="Shopify OAuth helper for Dev Dashboard apps")
    parser.add_argument("--shop", help="Shop domain (e.g., coaihome.myshopify.com)")
    parser.add_argument("--app-url", help="Public app URL (e.g., https://your-app.example.com)")
    parser.add_argument("--redirect-uri", help="Explicit redirect URI override")
    parser.add_argument("--scopes", help="OAuth scopes override")
    parser.add_argument("--install-url", action="store_true", help="Print OAuth install URL")
    parser.add_argument("--exchange", metavar="CODE", help="Exchange OAuth code for token")
    parser.add_argument("--save-env", action="store_true", help="Save token to .env")
    parser.add_argument("--env-file", default=".env", help="Env file path (default: .env)")
    parser.add_argument("--test", action="store_true", help="Test token after exchange")
    args = parser.parse_args()

    config = _load_config(args)

    if args.install_url or not args.exchange:
        try:
            oauth_url, state = _build_install_url(config)
            print("=" * 70)
            print("SHOPIFY OAUTH INSTALL URL")
            print("=" * 70)
            print()
            print(oauth_url)
            print()
            print(f"state={state}")
            print()
            print("After approving the app, copy the `code` from the callback URL and run:")
            print("python get_shopify_access_token.py --exchange YOUR_CODE --save-env --test")
            print("=" * 70)
            print()
        except Exception as exc:
            print(f"Error: {exc}")
            return

        if not args.exchange:
            return

    try:
        token = asyncio.run(_exchange_code(config, args.exchange))
        print("=" * 70)
        print("OAUTH TOKEN EXCHANGED SUCCESSFULLY")
        print("=" * 70)
        print()
        print(f"SHOPIFY_ACCESS_TOKEN={token}")
        print()

        if args.save_env:
            _upsert_env(args.env_file, "SHOPIFY_SHOP_URL", config["shop"])
            _upsert_env(args.env_file, "SHOPIFY_ACCESS_TOKEN", token)
            print(f"Saved SHOPIFY_ACCESS_TOKEN to {args.env_file}")
            print()

        if args.test or args.save_env:
            ok = asyncio.run(_test_token(config["shop"], token, config["api_version"]))
            print(f"Token test: {'PASS' if ok else 'FAIL'}")
            print()
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
