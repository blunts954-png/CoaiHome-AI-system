#!/usr/bin/env python
"""Check system configuration status"""
import os
from dotenv import load_dotenv

# Force reload .env before importing settings
load_dotenv(override=True)

print("=== RAW ENVIRONMENT ===")
print(f"SHOPIFY_SHOP_URL: {os.getenv('SHOPIFY_SHOP_URL', 'NOT SET')}")
print(f"SHOPIFY_API_KEY: {'SET' if os.getenv('SHOPIFY_API_KEY') else 'NOT SET'}")
print(f"STORE_BRAND_NAME: {os.getenv('STORE_BRAND_NAME', 'NOT SET')}")
print()

# Clear settings cache and reload
from config.settings import get_settings, Settings
from functools import lru_cache
get_settings.cache_clear()

# Force new settings load
settings = get_settings()

print("=== SETTINGS OBJECT ===")
print(f"Shopify Shop URL: {settings.shopify.shop_url or 'NOT SET'}")
print(f"Shopify API Key: {'SET' if settings.shopify.api_key else 'NOT SET'}")
print(f"Store Brand: {settings.store.brand_name or 'NOT SET'}")
print(f"Store Niche: {settings.store.niche or 'NOT SET'}")
print()

print("=== AVAILABILITY ===")
ai_ok = settings.ai.api_key and settings.ai.api_key != "your_openai_api_key_here"
shopify_ok = bool(settings.shopify.shop_url and settings.shopify.api_key)
print(f"Shopify Ready: {shopify_ok}")
print(f"AI Ready: {ai_ok}")
