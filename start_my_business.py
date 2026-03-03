"""
🚀 START YOUR DROPSHIPPING BUSINESS
One-click startup script - no technical knowledge needed!
"""
import subprocess
import sys
import os
import time
import webbrowser

from automation.utils import _configure_utf8_console

_configure_utf8_console()


def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  No .env file found!")
        print("\nCreating .env file template...")
        
        env_content = """# Required: Shopify (Get from Shopify Admin -> Apps -> Private apps)
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_admin_api_token

# Required: AI (Get from openai.com)
AI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4o-mini

# Optional: AutoDS Login (for browser automation)
AUTODS_EMAIL=your_autods_email@example.com
AUTODS_PASSWORD=your_autods_password

# Optional: Store Settings
STORE_NICHE=home organization
STORE_BRAND_NAME=CoaiHome
STORE_BASE_MARKUP=2.5
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file template!")
        print("\n📝 EDIT the .env file and add your credentials:")
        print("   1. SHOPIFY_SHOP_URL - yourstore.myshopify.com")
        print("   2. SHOPIFY_ACCESS_TOKEN - from Shopify Admin")
        print("   3. AI_API_KEY - from openai.com")
        print("\nThen run this script again!")
        return False
    return True

def main():
    print("=" * 60)
    print("🚀 AI DROPSHIPPING AUTOMATION SYSTEM")
    print("=" * 60)
    print()
    
    # Check environment
    if not check_env_file():
        input("\nPress Enter to exit...")
        return
    
    # Check if dependencies installed
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencies installed")
    except ImportError:
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", 
                       "fastapi", "uvicorn", "httpx", "pydantic-settings", 
                       "jinja2", "sqlalchemy", "schedule"])
        print("✅ Dependencies installed")
    
    print()
    print("🌐 Starting server...")
    print("   Dashboard will open automatically")
    print("   Press Ctrl+C to stop")
    print()
    print("=" * 60)
    
    # Start server
    try:
        # Open browser after 3 seconds
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:8000')
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start the server
        subprocess.run([sys.executable, "main.py"])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        print("Thanks for using AI Dropshipping Automation!")

if __name__ == "__main__":
    main()
