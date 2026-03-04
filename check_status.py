"""
AI Dropshipping System - Diagnostics & Health Check
Validates core dependencies, credentials, and connectivity.
Run this after deployment or when troubleshooting.
"""
import os
import sys
import asyncio
import httpx
from sqlalchemy import text
from typing import Dict, List, Tuple

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from models.database import SessionLocal, init_db, ShopifyInstallation
from services.shopify_oauth_store import get_any_installation

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(msg: str):
    print(f"{Colors.BOLD}🔍 {msg}...{Colors.ENDC}", end="", flush=True)

def print_pass(detail: str = ""):
    print(f" {Colors.OKGREEN}✅ PASS{Colors.ENDC} {detail}")

def print_fail(detail: str = ""):
    print(f" {Colors.FAIL}❌ FAIL{Colors.ENDC} {detail}")

def print_warn(detail: str = ""):
    print(f" {Colors.WARNING}⚠️  WARN{Colors.ENDC} {detail}")

async def check_database() -> bool:
    print_step("Checking Database")
    try:
        # ensure tables exist
        init_db()
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print_pass("Connected and Schema Valid")
        return True
    except Exception as e:
        print_fail(f"Could not connect to database: {e}")
        return False

async def check_shopify() -> bool:
    print_step("Checking Shopify Readiness")
    try:
        url = settings.shopify.shop_url
        token = settings.shopify.access_token
        
        # Check if we have a persisted installation as fallback
        persisted = get_any_installation()
        
        if not url and not persisted:
            print_fail("SHOPIFY_SHOP_URL is not set and no installations found in DB.")
            return False
            
        target_shop = url or persisted.shop
        target_token = token or (persisted.access_token if persisted else None)
        
        if not target_token:
            print_warn(f"Shop identified ({target_shop}) but no access token/installation found.")
            return True # Not a fatal blocker for the script itself but a warning for operation
            
        print_pass(f"Shop '{target_shop}' configured/installed.")
        return True
    except Exception as e:
        print_fail(f"Shopify check error: {e}")
        return False

async def check_cj() -> bool:
    print_step("Checking CJ Dropshipping")
    if not settings.cj.api_token:
        print_warn("CJ_API_TOKEN is missing. System will run in Shopify-only mode.")
        return True
    
    # Try a simple balance or profile call to validate token
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"CJ-Access-Token": settings.cj.api_token}
            # Test endpoint
            resp = await client.get(f"{settings.cj.base_url}/shop/getProfile", headers=headers)
            if resp.status_code == 200:
                print_pass("CJ API token validated")
                return True
            else:
                print_fail(f"CJ API token invalid (HTTP {resp.status_code})")
                return False
    except Exception as e:
        print_fail(f"CJ API connection error: {e}")
        return False

async def check_ai() -> bool:
    print_step("Checking AI (OpenAI/Anthropic)")
    if not settings.ai.api_key:
        print_warn("AI_API_KEY is missing. Product research/SEO features will be limited.")
        return True
    print_pass("API key present")
    return True

async def run_diagnostics():
    print(f"\n{Colors.HEADER}=== AI DROPSHIPPING SYSTEM DIAGNOSTICS ==={Colors.ENDC}\n")
    
    results = await asyncio.gather(
        check_database(),
        check_shopify(),
        check_cj(),
        check_ai()
    )
    
    print("\n" + "="*50)
    if all(results):
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🚀 SYSTEM READY FOR OPERATION{Colors.ENDC}")
        print("You can now run the automation loop or build your store.")
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}🚧 SYSTEM HAS BLOCKERS{Colors.ENDC}")
        print("Review the FAIL/WARN items above and update your environment variables.")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
