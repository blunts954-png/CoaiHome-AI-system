#!/usr/bin/env python
"""Verify credentials are loaded correctly"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

from config.settings import get_settings
get_settings.cache_clear()
settings = get_settings()

print("=== CREDENTIALS CHECK ===")
ai_key = settings.ai.api_key
if ai_key and ai_key != "your_openai_api_key_here":
    print(f"OpenAI Key: SET ({len(ai_key)} chars)")
else:
    print("OpenAI Key: NOT SET")

print(f"Shopify Shop: {settings.shopify.shop_url}")
print(f"Shopify Access Token: {'SET' if settings.shopify.access_token else 'NOT SET - API MODE UNAVAILABLE'}")
print(f"AI Model: {settings.ai.model}")
print()
print("NOTE: Full Shopify API mode requires one of these:")
print("  1) SHOPIFY_ACCESS_TOKEN (from custom app install), or")
print("  2) OAuth install flow with SHOPIFY_API_KEY + SHOPIFY_API_SECRET")
print("OAuth helper: python get_shopify_access_token.py --install-url")
