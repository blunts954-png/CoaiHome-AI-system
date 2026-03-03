"""Create deployment package for easy Shopify deployment"""
import csv
import os
import shutil
import sys

sys.path.insert(0, '.')

from models.database import SessionLocal, Product, ProductStatus

def create_deploy_package():
    print("Creating deployment package...")
    print()
    
    # Create folders
    os.makedirs('DEPLOY_PACKAGE/pages', exist_ok=True)
    os.makedirs('DEPLOY_PACKAGE/product_images', exist_ok=True)
    
    # Get products
    db = SessionLocal()
    products = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).all()
    
    # Create CSV
    print(f"Creating CSV with {len(products)} products...")
    csv_data = []
    for p in products:
        compare_price = round(p.selling_price * 1.4, 2)
        handle = p.title.lower().replace(' ', '-').replace(',', '').replace('"', '')[:50]
        
        csv_data.append({
            'Handle': handle,
            'Title': p.title,
            'Body (HTML)': p.description or '',
            'Vendor': 'CoaiHome',
            'Type': 'Home Organization',
            'Tags': 'organizer, home, storage',
            'Published': 'TRUE',
            'Option1 Name': 'Title',
            'Option1 Value': 'Default Title',
            'Variant SKU': f'COAI-{p.id:03d}',
            'Variant Grams': '500',
            'Variant Inventory Tracker': 'shopify',
            'Variant Inventory Qty': '100',
            'Variant Inventory Policy': 'deny',
            'Variant Fulfillment Service': 'manual',
            'Variant Price': str(p.selling_price),
            'Variant Compare At Price': str(compare_price),
            'Variant Requires Shipping': 'TRUE',
            'Variant Taxable': 'TRUE',
            'Image Src': '',
            'Status': 'active'
        })
    
    with open('DEPLOY_PACKAGE/shopify_import.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
        writer.writeheader()
        writer.writerows(csv_data)
    
    print("Created: DEPLOY_PACKAGE/shopify_import.csv")
    print()
    
    # Create CSS file
    css_content = """/* CoaiHome Theme CSS */
:root{--trust:#2563EB;--action:#F97316;--money:#10B981}
.btn-primary,.add-to-cart{background:var(--action)!important;color:#fff!important;border-radius:8px!important;padding:14px 32px!important;font-weight:600!important}
.checkout-button{background:var(--money)!important;color:#fff!important;padding:16px 40px!important;font-size:18px!important;font-weight:700!important}
.product-price{color:var(--action);font-size:20px;font-weight:700}
.scarcity-badge{background:#FEE2E2;color:#DC2626;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:700}
.site-header{background:var(--trust)}"""
    
    with open('DEPLOY_PACKAGE/css.txt', 'w') as f:
        f.write(css_content)
    
    print("Created: DEPLOY_PACKAGE/css.txt")
    print()
    
    # Create theme settings
    theme_content = """THEME SETTINGS FOR COAIHOME
============================

1. Go to: Online Store > Themes > Customize > Theme Settings

2. COLORS:
   Primary: #2563EB
   Secondary: #F97316
   Success: #10B981
   Background: #FFFFFF
   Text: #1A1A2E

3. TYPOGRAPHY:
   Heading Font: Poppins
   Body Font: Inter
   Base Size: 16px

4. CUSTOM CSS: Copy from css.txt
"""
    
    with open('DEPLOY_PACKAGE/theme_settings.txt', 'w') as f:
        f.write(theme_content)
    
    print("Created: DEPLOY_PACKAGE/theme_settings.txt")
    print()
    
    # Copy pages
    if os.path.exists('store_content/pages'):
        for file in os.listdir('store_content/pages'):
            src = f'store_content/pages/{file}'
            dst = f'DEPLOY_PACKAGE/pages/{file}'
            shutil.copy(src, dst)
        print(f"Copied {len(os.listdir('store_content/pages'))} page files")
    
    # Create README
    readme = """COAIHOME - DEPLOYMENT PACKAGE
==============================

QUICK START (5 Steps):

STEP 1: IMPORT PRODUCTS
- Go to Shopify Admin > Products > Import
- Upload: shopify_import.csv
- All 15 products will be created

STEP 2: SET THEME COLORS
- Go to Online Store > Themes > Customize
- Theme Settings > Colors
- Set: Primary #2563EB, Secondary #F97316, Success #10B981

STEP 3: ADD CUSTOM CSS
- Theme Settings > Custom CSS
- Copy contents of css.txt
- Save

STEP 4: CREATE PAGES
- Online Store > Pages
- Create each page using files in pages/ folder
- Copy HTML content from each file

STEP 5: LAUNCH
- Remove password protection
- Your store is LIVE!

FILES IN THIS PACKAGE:
- shopify_import.csv - Product import file
- css.txt - Custom CSS code
- theme_settings.txt - Color settings
- pages/ - 6 HTML page files

FULL GUIDE: See COMPLETE_STORE_DEPLOY_GUIDE.md
"""
    
    with open('DEPLOY_PACKAGE/README.txt', 'w') as f:
        f.write(readme)
    
    print("Created: DEPLOY_PACKAGE/README.txt")
    print()
    
    db.close()
    
    print("=" * 60)
    print("DEPLOY PACKAGE READY!")
    print("=" * 60)
    print()
    print("Location: DEPLOY_PACKAGE/")
    print()
    print("To deploy your store:")
    print("1. Open DEPLOY_PACKAGE/ folder")
    print("2. Follow README.txt")
    print("3. Import the CSV file")
    print("4. Copy the CSS")
    print("5. Launch!")

if __name__ == "__main__":
    create_deploy_package()
