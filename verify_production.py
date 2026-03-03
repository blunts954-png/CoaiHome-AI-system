#!/usr/bin/env python
"""Verify production configuration"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from config.settings import get_settings
get_settings.cache_clear()
settings = get_settings()

print("=== PRODUCTION CONFIGURATION ===")
print(f"Shopify Shop: {settings.shopify.shop_url}")
print(f"Shopify API Key: {'SET' if settings.shopify.api_key else 'NOT SET'}")
print(f"Shopify API Secret: {'SET' if settings.shopify.api_secret else 'NOT SET'}")
print(f"Shopify Access Token: {'SET' if settings.shopify.access_token else 'NOT SET'}")
print(f"Shopify App URL: {settings.shopify.app_url or 'NOT SET'}")
print(f"AI API Key: {'SET' if settings.ai.api_key else 'NOT SET'}")
print()

# OAuth URL validation
if settings.shopify.app_url:
    callback_url = f"{settings.shopify.app_url.rstrip('/')}/auth/shopify/callback"
    print("=== OAUTH CONFIGURATION ===")
    print(f"Install URL: {settings.shopify.app_url}/auth/shopify/install?shop={settings.shopify.shop_url}")
    print(f"Callback URL: {callback_url}")
    print()
    print("=== REQUIRED SHOPIFY APP SETTINGS ===")
    print(f"App URL: {settings.shopify.app_url}")
    print(f"Allowed redirect URL: {callback_url}")
else:
    print("WARNING: SHOPIFY_APP_URL not set!")
