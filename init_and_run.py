"""
Initialize database and start server
For Railway deployment
"""
import os
import sys

from automation.utils import _configure_utf8_console

_configure_utf8_console()


def main():
    print("=" * 60)
    print("🚀 AI DROPSHIPPING SYSTEM - RAILWAY DEPLOYMENT")
    print("=" * 60)
    print()
    
    # Import here after env vars are loaded
    try:
        from config.settings import settings
    except Exception as e:
        print(f"⚠️  Settings load error: {e}")
    
    # Check required env vars
    shop_url = os.getenv("SHOPIFY_SHOP_URL", "")
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
    ai_key = os.getenv("AI_API_KEY", "")
    
    print("📋 Environment Check:")
    print(f"  Shopify URL: {'✅ Set' if shop_url else '❌ Missing'}")
    print(f"  Access Token: {'✅ Set' if access_token else '❌ Missing'}")
    print(f"  AI API Key: {'✅ Set' if ai_key else '❌ Missing'}")
    
    if not shop_url:
        print()
        print("⚠️  WARNING: SHOPIFY_SHOP_URL not set!")
        print("   Set it in Railway dashboard: Settings → Variables")
    
    if not access_token and not os.getenv("SHOPIFY_API_KEY"):
        print()
        print("⚠️  WARNING: No Shopify credentials found!")
        print("   Set either:")
        print("   - SHOPIFY_ACCESS_TOKEN (for admin API)")
        print("   - SHOPIFY_API_KEY + SHOPIFY_API_SECRET (for OAuth)")
    
    print()
    print("🗄️  Initializing database...")
    
    try:
        # Initialize database
        from models.database import init_db
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database warning: {e}")
        print("   Continuing anyway...")
    
    print()
    print("🌐 Starting server...")
    print("=" * 60)
    
    # Start the main application
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
