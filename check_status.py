#!/usr/bin/env python
"""
Deep system diagnostics for the CoaiHome AI system.

Exit codes:
  0 — all checks passed
  1 — one or more FAIL-level checks (operational blocker)

Usage:
  python check_status.py
"""
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, List, Tuple

# Force .env load before any settings import
from dotenv import load_dotenv
load_dotenv(override=True)


@dataclass
class CheckResult:
    name: str
    level: str        # "PASS" | "FAIL" | "WARN"
    detail: str
    fix: str = ""

    @property
    def passed(self) -> bool:
        return self.level == "PASS"

    @property
    def icon(self) -> str:
        return {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(self.level, "❓")


def _mask(value: str, keep: int = 6) -> str:
    if not value:
        return "NOT SET"
    if len(value) <= keep:
        return "*" * len(value)
    return f"{'*' * (len(value) - keep)}{value[-keep:]}"


# ─────────────────────────────────────────────────────────────────────────────
# Individual checks
# ─────────────────────────────────────────────────────────────────────────────

def check_env_shopify() -> CheckResult:
    """Critical: Shopify shop URL + access token must be set."""
    from config.settings import get_settings
    s = get_settings()

    missing = []
    if not s.shopify.shop_url:
        missing.append("SHOPIFY_SHOP_URL")
    if not s.shopify.access_token:
        missing.append("SHOPIFY_ACCESS_TOKEN")

    if missing:
        return CheckResult(
            name="Shopify credentials",
            level="FAIL",
            detail=f"Not set: {', '.join(missing)}",
            fix=(
                "Add these to Railway Variables:\n"
                "  SHOPIFY_SHOP_URL = j2kjhy-ni.myshopify.com\n"
                "  SHOPIFY_ACCESS_TOKEN = shpat_...\n"
                "Then redeploy."
            ),
        )
    return CheckResult(
        name="Shopify credentials",
        level="PASS",
        detail=f"shop={s.shopify.shop_url}, token={_mask(s.shopify.access_token)}",
    )


def check_env_cj() -> CheckResult:
    """Warn: CJ credentials enable full automation mode."""
    from config.settings import get_settings
    from automation.utils import parse_cj_credentials
    s = get_settings()

    parsed = parse_cj_credentials(
        cj_token=s.cj.api_token,
        cj_email=s.cj.api_email,
        cj_key=s.cj.api_key,
    )
    if parsed["is_valid"]:
        return CheckResult(
            name="CJ Dropshipping credentials",
            level="PASS",
            detail=f"email={parsed['email']}, key={_mask(parsed['api_key'])}",
        )
    return CheckResult(
        name="CJ Dropshipping credentials",
        level="WARN",
        detail="CJ not configured — system runs in SHOPIFY-ONLY mode",
        fix=(
            "Add to Railway Variables:\n"
            "  CJ_API_TOKEN = yourEmail@api@yourApiKey\n"
            "  SYSTEM_SUPPLIER_PLATFORM = cj"
        ),
    )


def check_env_ai() -> CheckResult:
    """Warn: AI key enables product descriptions, TikTok scripts, etc."""
    from config.settings import get_settings
    s = get_settings()
    key = s.ai.api_key or ""
    if key and key != "your_openai_api_key_here":
        return CheckResult(
            name="AI API key (OpenAI)",
            level="PASS",
            detail=f"Key: {_mask(key)}",
        )
    return CheckResult(
        name="AI API key (OpenAI)",
        level="WARN",
        detail="AI_API_KEY not set — AI content generation disabled",
        fix="Add AI_API_KEY = sk-... to Railway Variables",
    )


def check_database() -> CheckResult:
    """Critical: DB must be reachable."""
    try:
        from sqlalchemy import text
        from models.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return CheckResult(
            name="Database connectivity",
            level="PASS",
            detail=f"Connected ({engine.url.drivername})",
        )
    except Exception as exc:
        return CheckResult(
            name="Database connectivity",
            level="FAIL",
            detail=f"Connection failed: {exc}",
            fix="Set DATABASE_URL in Railway Variables and ensure DB is provisioned.",
        )


def check_tables() -> CheckResult:
    """Critical: All schema tables must exist."""
    required = {
        "stores", "products", "price_changes", "product_research_jobs",
        "order_exceptions", "supplier_performance", "system_logs",
        "customer_support_tickets", "shop_installs", "oauth_states",
    }
    try:
        from sqlalchemy import inspect as sa_inspect
        from models.database import engine
        found = set(sa_inspect(engine).get_table_names())
    except Exception as exc:
        return CheckResult(
            name="Database schema",
            level="FAIL",
            detail=f"Cannot inspect schema: {exc}",
            fix='Run: python -c "from models.database import init_db; init_db()"',
        )

    missing = sorted(required - found)
    if missing:
        return CheckResult(
            name="Database schema",
            level="FAIL",
            detail=f"Missing tables: {', '.join(missing)}",
            fix='Run: python -c "from models.database import init_db; init_db()" then restart.',
        )
    return CheckResult(
        name="Database schema",
        level="PASS",
        detail=f"All {len(required)} required tables present",
    )


def check_oauth_persistence() -> CheckResult:
    """Critical: shop_installs must be accessible (replaces in-memory INSTALLED_SHOPS)."""
    try:
        from models.database import SessionLocal, ShopInstall
        db = SessionLocal()
        count = db.query(ShopInstall).count()
        db.close()
        return CheckResult(
            name="OAuth token persistence (DB-backed)",
            level="PASS",
            detail=f"shop_installs table accessible, {count} shop(s) stored",
        )
    except Exception as exc:
        return CheckResult(
            name="OAuth token persistence (DB-backed)",
            level="FAIL",
            detail=f"shop_installs not accessible: {exc}",
            fix='Run init_db() to create the table, then restart.',
        )


def check_cors() -> CheckResult:
    """Warn: Wildcard CORS is a security risk in production."""
    from config.settings import get_settings
    s = get_settings()
    if s.system.cors_allowed_origins:
        return CheckResult(
            name="CORS security",
            level="PASS",
            detail=f"Allowed origins: {s.system.cors_allowed_origins}",
        )
    if s.system.debug:
        return CheckResult(
            name="CORS security",
            level="WARN",
            detail="Wildcard CORS active (debug mode — acceptable locally)",
            fix="Set SYSTEM_CORS_ALLOWED_ORIGINS=https://your-railway-domain.up.railway.app",
        )
    return CheckResult(
        name="CORS security",
        level="WARN",
        detail="SYSTEM_CORS_ALLOWED_ORIGINS not set — cross-origin requests blocked in production",
        fix="Set SYSTEM_CORS_ALLOWED_ORIGINS=https://your-railway-domain.up.railway.app",
    )


def check_ssl() -> CheckResult:
    """Warn: SSL verification should be enabled outside local dev."""
    from config.settings import get_settings
    s = get_settings()
    if s.shopify.ssl_verify:
        return CheckResult(name="TLS / SSL verification", level="PASS", detail="Enabled")
    return CheckResult(
        name="TLS / SSL verification",
        level="WARN",
        detail="SHOPIFY_SSL_VERIFY=false disables TLS — unsafe in production",
        fix="Remove SHOPIFY_SSL_VERIFY from Railway Variables (default is true).",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

CHECKS: List[Callable[[], CheckResult]] = [
    check_env_shopify,
    check_env_cj,
    check_env_ai,
    check_database,
    check_tables,
    check_oauth_persistence,
    check_cors,
    check_ssl,
]


def run_checks() -> Tuple[List[CheckResult], int]:
    results = [c() for c in CHECKS]
    failures = sum(1 for r in results if r.level == "FAIL")
    return results, failures


def main() -> int:
    # Clear cached settings so .env override takes effect
    from config.settings import get_settings
    try:
        get_settings.cache_clear()
    except AttributeError:
        pass

    s = get_settings()

    print("=" * 66)
    print("  CoaiHome AI System — Configuration Diagnostics")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 66)
    print()
    print("=== RAW ENVIRONMENT (sanitized) ===")
    print(f"  SHOPIFY_SHOP_URL      : {s.shopify.shop_url or 'NOT SET'}")
    print(f"  SHOPIFY_ACCESS_TOKEN  : {_mask(s.shopify.access_token)}")
    print(f"  SHOPIFY_API_KEY       : {_mask(s.shopify.api_key)}")
    print(f"  CJ_API_TOKEN          : {_mask(s.cj.api_token)}")
    print(f"  AI_API_KEY            : {_mask(s.ai.api_key)}")
    print(f"  DATABASE_URL          : {s.system.database_url}")
    print(f"  SYSTEM_DEBUG          : {s.system.debug}")
    print(f"  SYSTEM_CORS_ORIGINS   : {s.system.cors_allowed_origins or '(not set)'}")
    print(f"  SHOPIFY_SSL_VERIFY    : {s.shopify.ssl_verify}")
    print()

    results, failures = run_checks()
    warns = sum(1 for r in results if r.level == "WARN")

    print("=== DIAGNOSTICS ===")
    for r in results:
        print(f"  {r.icon} [{r.level:4s}] {r.name}")
        print(f"         {r.detail}")
        if r.fix:
            for line in r.fix.strip().splitlines():
                print(f"         FIX: {line}")
    print()

    print("=== SUMMARY ===")
    print(f"  Checks : {len(results)}")
    print(f"  Passed : {len(results) - failures - warns}")
    print(f"  Warnings: {warns}")
    print(f"  Failures: {failures}")
    print()

    if failures == 0:
        print("  ✅ System is operationally ready.")
    else:
        print(f"  ❌ {failures} blocker(s) must be resolved before the system is production-ready.")

    print("=" * 66)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
