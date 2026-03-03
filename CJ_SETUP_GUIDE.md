# CJ Dropshipping Setup Guide

## Overview
Your CJ Dropshipping AI Automation system is now configured! Here's what has been set up:

---

## Configuration Complete

### API Credentials Configured
- **CJ API Email:** CJ5192487
- **CJ API Key:** 2933552063d344f682d8f3d8d2b32c10
- **Supplier Platform:** CJ Dropshipping
- **Store Niche:** Home Organization
- **Store Brand:** CoaiHome

### Files Created/Updated
1. `.env` - Environment variables with CJ credentials
2. `api_clients/cj_dropshipping_client.py` - Full CJ API client
3. `api_clients/autods_client.py` - Updated to support CJ mode
4. `config/settings.py` - CJ configuration settings
5. `start_cj_business.py` - Launch script for CJ automation

---

## Known Issue: SSL Certificate

**Status:** There is an SSL certificate verification issue when connecting to the CJ API endpoint (`developers.cjdropshipping.com`). This is likely due to:

1. Outdated SSL certificates on your Windows system
2. CJ API server certificate configuration
3. Network/firewall restrictions

### Solutions:

#### Option 1: Update System SSL Certificates (Recommended)
```powershell
# Run as Administrator
pip install --upgrade certifi
pip install --upgrade urllib3
```

#### Option 2: Use Manual Product Import Mode
The system works perfectly in "Shopify Direct" mode:
1. Research products on CJ Dropshipping website
2. Add products manually via the dashboard
3. The system handles pricing, content, and TikTok automation

#### Option 3: Contact CJ Support
Verify the correct API endpoint and SSL configuration with CJ Dropshipping support.

---

## How to Run Your Business

### Method 1: Web Dashboard (Recommended)
```bash
cd dropshipping_ai_system
python main.py
```
Then open: http://localhost:8000

### Method 2: Full Automation
```bash
cd dropshipping_ai_system
python start_cj_business.py
```

### Method 3: API Integration
Use the API endpoints directly:

#### Research Products
```bash
curl -X POST "http://localhost:8000/api/research/run?store_id=1&niche=home%20organization"
```

#### Check System Status
```bash
curl http://localhost:8000/api/system/status
```

#### Add Product Manually
```bash
curl -X POST "http://localhost:8000/api/products/manual-add" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Organizer Product",
    "description": "Great organizer",
    "cost_price": 10.00,
    "selling_price": 29.99,
    "supplier_name": "CJ Dropshipping",
    "supplier_url": "https://cjdropshipping.com/product/xxx"
  }'
```

---

## Features Available

### With CJ API (when SSL issue resolved):
- Automated product research from CJ catalog
- Direct product import to Shopify
- Inventory sync with CJ
- Order fulfillment tracking

### Without CJ API (Current Mode):
- Manual product research (TikTok, Google Trends, CJ website)
- Manual product import via dashboard
- AI-powered pricing optimization
- TikTok content generation
- Inventory monitoring via Shopify
- Order tracking
- Exception management

---

## Next Steps to Start Making Money

1. **Fix SSL Issue** (Optional but recommended)
   - Update certificates OR
   - Use manual product import mode

2. **Add Products to Your Store**
   - Go to CJ Dropshipping website
   - Find trending products in your niche
   - Use the dashboard to add them

3. **Generate TikTok Content**
   - Use the content calendar feature
   - Post daily to drive traffic

4. **Monitor and Optimize**
   - Check pricing daily
   - Monitor inventory levels
   - Fulfill orders promptly

---

## Important URLs

- **Dashboard:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **CJ Dropshipping:** https://cjdropshipping.com/

---

## Troubleshooting

### "SSL Certificate Error"
See "Known Issue: SSL Certificate" section above.

### "Shopify Mode Active"
- Check CJ_API_EMAIL and CJ_API_KEY in .env file
- Verify SYSTEM_SUPPLIER_PLATFORM=cj

### "Database Error"
```bash
cd dropshipping_ai_system
python -c "from models.database import init_db; init_db()"
```

### "Module Not Found"
```bash
pip install -r requirements.txt
```

---

## Support

For issues or questions:
1. Check the logs in the dashboard
2. Review this guide
3. Verify API credentials in `.env`
4. Contact CJ Dropshipping for API support

---

## Your Store Details

| Setting | Value |
|---------|-------|
| Platform | Shopify + CJ Dropshipping |
| Store URL | coaihome.myshopify.com |
| Niche | Home Organization |
| Brand | CoaiHome |
| Supplier | CJ Dropshipping |

---

**Ready to start!** Run `python main.py` and open http://localhost:8000
