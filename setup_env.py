"""
Interactive .env file setup helper
Run this to configure your system easily!
"""
import os

def main():
    print("=" * 60)
    print("🛠️  AI DROPSHIPPING - ENVIRONMENT SETUP")
    print("=" * 60)
    print()
    
    env_vars = {}
    
    # Shopify Store URL
    print("📦 SHOPIFY CONNECTION")
    print("-" * 40)
    shop_url = input("Your Shopify store URL (e.g., coaihome.myshopify.com): ").strip()
    if shop_url:
        # Remove https:// and trailing slashes
        shop_url = shop_url.replace("https://", "").replace("http://", "").rstrip("/")
        env_vars["SHOPIFY_SHOP_URL"] = shop_url
    
    print()
    print("You need ONE of these two options:")
    print()
    print("Option 1: Admin API Token (EASIEST - Recommended)")
    print("  → Full access to your own store")
    print("  → Get it from: Shopify Admin → Settings → Apps → Develop apps")
    print()
    print("Option 2: OAuth App Credentials")
    print("  → For letting others install your app")
    print("  → You already have these (Client ID + Secret)")
    print()
    
    choice = input("Which option? (1 or 2): ").strip()
    
    if choice == "1":
        access_token = input("Admin API Access Token (shpat_...): ").strip()
        if access_token:
            env_vars["SHOPIFY_ACCESS_TOKEN"] = access_token
    else:
        api_key = input("Client ID (from your app): ").strip()
        api_secret = input("Secret (from your app): ").strip()
        app_url = input("Your app URL (for OAuth callback): ").strip()
        
        if api_key:
            env_vars["SHOPIFY_API_KEY"] = api_key
        if api_secret:
            env_vars["SHOPIFY_API_SECRET"] = api_secret
        if app_url:
            env_vars["SHOPIFY_APP_URL"] = app_url
    
    print()
    print("🤖 AI CONFIGURATION")
    print("-" * 40)
    ai_key = input("OpenAI API Key (sk-...): ").strip()
    if ai_key:
        env_vars["AI_API_KEY"] = ai_key
    
    ai_model = input("AI Model (press Enter for gpt-4o-mini): ").strip()
    env_vars["AI_MODEL"] = ai_model if ai_model else "gpt-4o-mini"
    
    print()
    print("⚙️  STORE SETTINGS (Optional)")
    print("-" * 40)
    niche = input("Store niche (press Enter for 'home organization'): ").strip()
    env_vars["STORE_NICHE"] = niche if niche else "home organization"
    
    brand = input("Brand name (press Enter for 'CoaiHome'): ").strip()
    env_vars["STORE_BRAND_NAME"] = brand if brand else "CoaiHome"
    
    print()
    print("📝 Writing .env file...")
    
    # Write to .env file
    with open(".env", "w") as f:
        f.write("# AI Dropshipping Automation - Environment Variables\n")
        f.write("# Generated automatically\n\n")
        
        f.write("# Shopify Connection\n")
        for key in ["SHOPIFY_SHOP_URL", "SHOPIFY_ACCESS_TOKEN", "SHOPIFY_API_KEY", 
                    "SHOPIFY_API_SECRET", "SHOPIFY_APP_URL"]:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# AI Configuration\n")
        for key in ["AI_API_KEY", "AI_MODEL"]:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        f.write("\n# Store Settings\n")
        for key in ["STORE_NICHE", "STORE_BRAND_NAME"]:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
    
    print("✅ .env file created successfully!")
    print()
    print("🚀 You're ready to start!")
    print("   Run: python start_my_business.py")
    print()
    
    # Show what was configured
    print("📋 Configured values:")
    for key, value in env_vars.items():
        if "SECRET" in key or "TOKEN" in key or "KEY" in key:
            display_val = value[:10] + "..." if len(value) > 10 else value
            print(f"   {key}={display_val}")
        else:
            print(f"   {key}={value}")

if __name__ == "__main__":
    main()
