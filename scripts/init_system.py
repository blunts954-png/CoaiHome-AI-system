"""
Initialization script for the AI Dropshipping System
Run this to set up the database and verify configuration
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import init_db
from config.settings import settings


def check_config():
    """Verify required configuration is present"""
    errors = []
    warnings = []
    
    # Check Shopify config
    if not settings.shopify.shop_url:
        errors.append("SHOPIFY_SHOP_URL is required")
    if not settings.shopify.access_token:
        errors.append("SHOPIFY_ACCESS_TOKEN is required")
    
    # Check AutoDS config
    if not settings.autods.api_key:
        errors.append("AUTODS_API_KEY is required")
    
    # Check AI config
    if not settings.ai.api_key:
        errors.append("AI_API_KEY is required")
    
    # Warnings
    if not settings.notifications.email_enabled and not settings.notifications.slack_enabled:
        warnings.append("No notifications configured (email or slack)")
    
    if settings.system.require_approval_for_import:
        warnings.append("Product import requires manual approval")
    
    if settings.system.require_approval_for_price_changes:
        warnings.append("Price changes require manual approval")
    
    return errors, warnings


def main():
    print("=" * 60)
    print("AI Dropshipping Automation System - Initialization")
    print("=" * 60)
    
    # Check configuration
    print("\n🔍 Checking configuration...")
    errors, warnings = check_config()
    
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease set these in your .env file")
        sys.exit(1)
    
    print("✅ Configuration valid")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    # Initialize database
    print("\n🗄️  Initializing database...")
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ System ready to start!")
    print("=" * 60)
    print("\nTo start the system:")
    print("   python main.py")
    print("\nOr with Docker:")
    print("   docker-compose up -d")
    print("\nAccess the dashboard at: http://localhost:8000")


if __name__ == "__main__":
    main()
