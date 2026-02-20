"""
AI Dropshipping Automation System - Main Application
FastAPI backend with automated workflows
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uvicorn
import os
import hashlib
import hmac
import re
import secrets
from urllib.parse import urlencode
import httpx

from config.settings import settings


# Pydantic models for API
class StoreSpec(BaseModel):
    niche: str
    brand_name: str
    target_country: str = "US"
    brand_tone: str = "professional"
    primary_color: str = "#000000"
    secondary_color: str = "#ffffff"
    price_range: Dict[str, float] = {"min": 15.0, "max": 500.0}
    num_products: int = 10


class PriceChangeApproval(BaseModel):
    approve: bool


class ExceptionResolution(BaseModel):
    resolution: str
    resolved_by: str


class ContentRequest(BaseModel):
    content_type: str  # product_description, email_template, etc.
    context: Dict[str, Any]


SHOPIFY_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*\.myshopify\.com$")
OAUTH_STATE_STORE: Dict[str, str] = {}
INSTALLED_SHOPS: Dict[str, str] = {}


def _is_valid_shop_domain(shop: str) -> bool:
    return bool(SHOPIFY_DOMAIN_RE.match(shop))


def _build_hmac_message(request: Request) -> str:
    filtered = [(k, v) for k, v in request.query_params.multi_items() if k not in {"hmac", "signature"}]
    sorted_items = sorted(filtered, key=lambda item: item[0])
    return "&".join(f"{key}={value}" for key, value in sorted_items)


def _verify_shopify_hmac(request: Request, api_secret: str) -> bool:
    provided_hmac = request.query_params.get("hmac", "")
    if not provided_hmac:
        return False
    message = _build_hmac_message(request)
    digest = hmac.new(api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided_hmac)


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting CoaiHome AI System")
    
    # Initialize database
    try:
        from models.database import init_db
        print("🗄️  Initializing database...")
        init_db()
        print("✅ Database ready")
    except Exception as e:
        print(f"⚠️  Database warning: {e}")
    
    # Start scheduler (optional)
    try:
        from automation.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.start()
    except Exception as e:
        print(f"⚠️  Scheduler warning: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")


# Create app
app = FastAPI(
    title="AI Dropshipping Automation",
    description="AI-powered Shopify dropshipping automation system",
    version="1.0.0",
    lifespan=lifespan
)

# Templates
templates = Jinja2Templates(directory="web/templates")


# ============ Public Routes ============

@app.get("/", response_class=HTMLResponse)
async def root_redirect(request: Request):
    """Root redirects to dashboard (for personal use)"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ============ Dashboard Routes ============

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/exceptions", response_class=HTMLResponse)
async def exceptions_page(request: Request):
    """Exception queue page"""
    return templates.TemplateResponse("exceptions.html", {"request": request})


@app.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """Products management page"""
    return templates.TemplateResponse("products.html", {"request": request})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Pricing management page"""
    return templates.TemplateResponse("pricing.html", {"request": request})


# ============ Shopify OAuth ============ 

@app.get("/auth/shopify/install")
async def shopify_install(shop: str):
    """Start Shopify OAuth installation flow."""
    if not settings.shopify.api_key or not settings.shopify.api_secret:
        raise HTTPException(status_code=500, detail="Missing SHOPIFY_API_KEY or SHOPIFY_API_SECRET")
    if not settings.shopify.app_url:
        raise HTTPException(status_code=500, detail="Missing SHOPIFY_APP_URL")

    shop = shop.strip().lower()
    if not _is_valid_shop_domain(shop):
        raise HTTPException(status_code=400, detail="Invalid shop domain. Use format: store-name.myshopify.com")

    state = secrets.token_urlsafe(24)
    OAUTH_STATE_STORE[state] = shop
    callback_url = f"{settings.shopify.app_url.rstrip('/')}/auth/shopify/callback"
    query = urlencode(
        {
            "client_id": settings.shopify.api_key,
            "scope": settings.shopify.api_scopes,
            "redirect_uri": callback_url,
            "state": state
        }
    )
    install_url = f"https://{shop}/admin/oauth/authorize?{query}"
    return RedirectResponse(url=install_url, status_code=302)


@app.get("/auth/shopify/callback")
async def shopify_callback(request: Request):
    """Handle Shopify OAuth callback and exchange code for access token."""
    if not settings.shopify.api_key or not settings.shopify.api_secret:
        raise HTTPException(status_code=500, detail="Missing SHOPIFY_API_KEY or SHOPIFY_API_SECRET")

    shop = request.query_params.get("shop", "").strip().lower()
    code = request.query_params.get("code", "")
    state = request.query_params.get("state", "")

    if not shop or not code or not state:
        raise HTTPException(status_code=400, detail="Missing required OAuth parameters")
    if not _is_valid_shop_domain(shop):
        raise HTTPException(status_code=400, detail="Invalid shop domain")
    if OAUTH_STATE_STORE.pop(state, None) != shop:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if not _verify_shopify_hmac(request, settings.shopify.api_secret):
        raise HTTPException(status_code=400, detail="Invalid OAuth HMAC signature")

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": settings.shopify.api_key,
        "client_secret": settings.shopify.api_secret,
        "code": code
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(token_url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {response.text}")

    access_token = response.json().get("access_token", "")
    if not access_token:
        raise HTTPException(status_code=502, detail="Token exchange failed: missing access_token")

    # Runtime-only cache so this process can immediately call Shopify APIs.
    settings.shopify.shop_url = shop
    settings.shopify.access_token = access_token
    INSTALLED_SHOPS[shop] = access_token

    return RedirectResponse(url=f"/dashboard?shop={shop}&installed=1", status_code=302)


@app.get("/auth/shopify/status")
async def shopify_install_status(shop: str):
    """Check whether this process has an installed token cached for a shop."""
    shop = shop.strip().lower()
    return {"shop": shop, "installed": shop in INSTALLED_SHOPS}


# ============ API Routes - Store Builder ============

@app.post("/api/stores/create")
async def create_store(spec: StoreSpec, background_tasks: BackgroundTasks):
    """Create a new AI-built store"""
    from automation.store_builder import get_store_builder
    builder = get_store_builder()
    
    # Run in background as it takes time
    result = await builder.create_store_from_spec(spec.dict())
    
    return result


@app.get("/api/stores")
async def list_stores():
    """List all stores"""
    from models.database import SessionLocal, Store
    db = SessionLocal()
    stores = db.query(Store).all()
    db.close()
    
    return {
        "stores": [
            {
                "id": s.id,
                "brand_name": s.brand_name,
                "niche": s.niche,
                "domain": s.shopify_domain,
                "autods_connected": s.autods_connected,
                "created_at": s.created_at.isoformat()
            }
            for s in stores
        ]
    }


# ============ API Routes - Product Research ============

@app.post("/api/research/run")
async def run_research(store_id: int, niche: Optional[str] = None):
    """Trigger a product research job"""
    from automation.product_research import get_product_research
    research = get_product_research()
    result = await research.run_research_job(store_id, niche)
    return result


@app.get("/api/research/jobs")
async def list_research_jobs(store_id: Optional[int] = None):
    """List product research jobs"""
    from models.database import SessionLocal, ProductResearchJob
    db = SessionLocal()
    query = db.query(ProductResearchJob)
    if store_id:
        query = query.filter(ProductResearchJob.store_id == store_id)
    jobs = query.order_by(ProductResearchJob.created_at.desc()).limit(20).all()
    db.close()
    
    return {
        "jobs": [
            {
                "id": j.id,
                "store_id": j.store_id,
                "niche": j.niche,
                "status": j.status,
                "products_found": j.products_found,
                "products_selected": j.products_selected,
                "products_imported": j.products_imported,
                "created_at": j.created_at.isoformat()
            }
            for j in jobs
        ]
    }


@app.get("/api/products/pending")
async def get_pending_products(store_id: Optional[int] = None):
    """Get products pending approval"""
    from models.database import SessionLocal, Product
    db = SessionLocal()
    query = db.query(Product).filter(Product.status == "pending_approval")
    if store_id:
        query = query.filter(Product.store_id == store_id)
    products = query.all()
    db.close()
    
    return {
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "cost_price": p.cost_price,
                "suggested_price": p.suggested_price,
                "supplier_name": p.supplier_name,
                "ai_confidence": p.ai_import_confidence,
                "created_at": p.created_at.isoformat()
            }
            for p in products
        ]
    }


@app.post("/api/products/{product_id}/approve")
async def approve_product(product_id: int):
    """Approve a pending product for import"""
    from automation.product_research import get_product_research
    research = get_product_research()
    result = await research.approve_pending_product(product_id)
    return result


@app.post("/api/products/{product_id}/reject")
async def reject_product(product_id: int, reason: Optional[str] = ""):
    """Reject a pending product"""
    from automation.product_research import get_product_research
    research = get_product_research()
    result = await research.reject_pending_product(product_id, reason)
    return result


# Manual product addition (for Shopify-only mode)
class ManualProduct(BaseModel):
    title: str
    description: str = ""
    cost_price: float
    selling_price: float
    supplier_name: str = ""
    supplier_url: str = ""  # AliExpress, CJ Dropshipping, etc.
    image_urls: List[str] = []
    tags: List[str] = []
    category: str = ""


@app.post("/api/products/manual-add")
async def add_product_manual(product: ManualProduct, store_id: int = 1):
    """
    Add a product manually (Shopify-only mode)
    Use this when you don't have AutoDS API access
    """
    from api_clients.autods_client import get_autods_client
    from models.database import SessionLocal, Product, ProductStatus, Store
    
    db = SessionLocal()
    store = db.query(Store).filter(Store.id == store_id).first()
    
    if not store:
        db.close()
        raise HTTPException(status_code=404, detail="Store not found")
    
    try:
        # Import directly to Shopify (bypassing AutoDS)
        autods = get_autods_client()
        
        import_data = {
            "title": product.title,
            "description": product.description,
            "cost_price": product.cost_price,
            "suggested_price": product.selling_price,
            "supplier_name": product.supplier_name,
            "tags": product.tags,
            "image_urls": product.image_urls,
            "category": product.category
        }
        
        result = await autods.import_product(import_data, store.shopify_domain)
        
        if result.get("success"):
            # Save to local DB
            db_product = Product(
                store_id=store_id,
                shopify_product_id=result.get("shopify_product_id"),
                autods_product_id=None,  # No AutoDS integration
                title=product.title,
                description=product.description,
                cost_price=product.cost_price,
                selling_price=product.selling_price,
                supplier_name=product.supplier_name,
                supplier_url=product.supplier_url,
                ai_import_confidence=1.0,  # Manual = high confidence
                status=ProductStatus.ACTIVE
            )
            db.add(db_product)
            db.commit()
            
            return {
                "status": "success",
                "message": "Product added successfully (Shopify-only mode)",
                "product_id": db_product.id,
                "shopify_product_id": result.get("shopify_product_id"),
                "note": "Fulfill orders manually or via AutoDS dashboard until API access is available"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "Import failed"))
            
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/list")
async def list_all_products(store_id: Optional[int] = None, status: Optional[str] = None):
    """List all products in the system"""
    from models.database import SessionLocal, Product
    
    db = SessionLocal()
    query = db.query(Product)
    
    if store_id:
        query = query.filter(Product.store_id == store_id)
    if status:
        query = query.filter(Product.status == status)
    
    products = query.order_by(Product.created_at.desc()).all()
    db.close()
    
    return {
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "cost_price": p.cost_price,
                "selling_price": p.selling_price,
                "profit_margin": round(((p.selling_price - p.cost_price) / p.selling_price * 100), 2) if p.selling_price else 0,
                "supplier_name": p.supplier_name,
                "status": p.status,
                "shopify_product_id": p.shopify_product_id,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in products
        ],
        "total": len(products),
        "mode": "SHOPIFY-ONLY (AutoDS API not configured)" if not settings.autods.api_key else "FULL MODE"
    }


@app.get("/api/shopify/products")
async def get_shopify_products(limit: int = 50):
    """Fetch products directly from Shopify"""
    from api_clients.shopify_client import get_shopify_client
    
    try:
        shopify = get_shopify_client()
        result = await shopify.list_products(limit=limit)
        
        products = result.get("products", [])
        return {
            "products": [
                {
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "vendor": p.get("vendor"),
                    "product_type": p.get("product_type"),
                    "status": p.get("status"),
                    "price": p.get("variants", [{}])[0].get("price") if p.get("variants") else None,
                    "inventory": p.get("variants", [{}])[0].get("inventory_quantity") if p.get("variants") else None
                }
                for p in products
            ],
            "count": len(products)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/shopify/orders")
async def get_shopify_orders(limit: int = 50, status: str = "any"):
    """Fetch orders directly from Shopify"""
    from api_clients.shopify_client import get_shopify_client
    
    try:
        shopify = get_shopify_client()
        result = await shopify.list_orders(limit=limit, status=status)
        
        orders = result.get("orders", [])
        return {
            "orders": [
                {
                    "id": o.get("id"),
                    "order_number": o.get("name"),
                    "total_price": o.get("total_price"),
                    "financial_status": o.get("financial_status"),
                    "fulfillment_status": o.get("fulfillment_status"),
                    "created_at": o.get("created_at"),
                    "customer": o.get("customer", {}).get("email") if o.get("customer") else None
                }
                for o in orders
            ],
            "count": len(orders)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/status")
async def get_system_status():
    """Get system configuration status"""
    return {
        "mode": "SHOPIFY-ONLY" if not settings.autods.api_key else "FULL",
        "shopify_connected": bool(settings.shopify.shop_url and settings.shopify.access_token),
        "autods_connected": bool(settings.autods.api_key),
        "features": {
            "product_research": "MANUAL" if not settings.autods.api_key else "AUTOMATED",
            "product_import": "SHOPIFY_DIRECT" if not settings.autods.api_key else "AUTODS",
            "auto_fulfillment": "MANUAL" if not settings.autods.api_key else "AUTOMATED",
            "pricing_optimization": "AVAILABLE",
            "ai_content": "AVAILABLE",
            "inventory_sync": "SHOPIFY_ONLY" if not settings.autods.api_key else "FULL"
        },
        "setup_instructions": None if settings.autods.api_key else [
            "1. Find products on AliExpress/CJ Dropshipping/Spocket",
            "2. Use POST /api/products/manual-add to add products",
            "3. Manage orders via Shopify admin or AutoDS dashboard",
            "4. Get AutoDS API key for full automation"
        ]
    }


# ============ API Routes - Pricing ============

@app.post("/api/pricing/optimize")
async def run_pricing_optimization(store_id: Optional[int] = None):
    """Run AI pricing optimization"""
    from automation.pricing_engine import get_pricing_engine
    engine = get_pricing_engine()
    result = await engine.run_pricing_optimization(store_id)
    return result


@app.get("/api/pricing/pending")
async def get_pending_price_changes(store_id: Optional[int] = None):
    """Get pending price changes"""
    from models.database import SessionLocal, PriceChange, Product
    db = SessionLocal()
    query = db.query(PriceChange).filter(PriceChange.status == "pending")
    if store_id:
        query = query.join(Product).filter(Product.store_id == store_id)
    changes = query.all()
    db.close()
    
    return {
        "price_changes": [
            {
                "id": c.id,
                "product_id": c.product_id,
                "product_title": c.product.title if c.product else "Unknown",
                "old_price": c.old_price,
                "suggested_price": c.suggested_price,
                "change_percent": ((c.suggested_price - c.old_price) / c.old_price * 100),
                "ai_reasoning": c.ai_reasoning,
                "confidence_score": c.confidence_score,
                "created_at": c.created_at.isoformat()
            }
            for c in changes
        ]
    }


@app.post("/api/pricing/{price_change_id}/approve")
async def approve_price_change(price_change_id: int):
    """Approve a pending price change"""
    from automation.pricing_engine import get_pricing_engine
    engine = get_pricing_engine()
    result = await engine.approve_price_change(price_change_id)
    return result


@app.post("/api/pricing/{price_change_id}/reject")
async def reject_price_change(price_change_id: int):
    """Reject a pending price change"""
    from automation.pricing_engine import get_pricing_engine
    engine = get_pricing_engine()
    result = await engine.reject_price_change(price_change_id)
    return result


# ============ API Routes - Fulfillment ============

@app.get("/api/exceptions")
async def get_exceptions(status: str = "open"):
    """Get fulfillment exceptions"""
    from automation.fulfillment_monitor import get_fulfillment_monitor
    monitor = get_fulfillment_monitor()
    exceptions = await monitor.get_exception_queue(status)
    return {"exceptions": exceptions}


@app.post("/api/exceptions/{exception_id}/resolve")
async def resolve_exception(exception_id: int, resolution: ExceptionResolution):
    """Resolve a fulfillment exception"""
    from automation.fulfillment_monitor import get_fulfillment_monitor
    monitor = get_fulfillment_monitor()
    result = await monitor.resolve_exception(
        exception_id,
        resolution.resolution,
        resolution.resolved_by
    )
    return result


@app.post("/api/inventory/sync")
async def sync_inventory(store_id: Optional[int] = None):
    """Manually trigger inventory sync"""
    try:
        from automation.fulfillment_monitor import get_fulfillment_monitor
        monitor = get_fulfillment_monitor()
        result = await monitor.run_inventory_sync(store_id)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e), "stock_updates": 0}


# ============ API Routes - AI Content ============

@app.post("/api/ai/generate-content")
async def generate_content(request: ContentRequest):
    """Generate AI content (descriptions, emails, etc.)"""
    from services.ai_service import get_ai_service
    ai = get_ai_service()
    
    if request.content_type == "product_description":
        result = await ai.generate_product_description(
            request.context.get("product_info", {}),
            request.context.get("brand_tone", "professional")
        )
    elif request.content_type == "store_content":
        result = await ai.generate_store_content(request.context)
    elif request.content_type == "email_template":
        result = await ai.generate_email_template(
            request.context.get("email_type", "general"),
            request.context
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown content type")
    
    return result


# ============ API Routes - TikTok Content ============

class TikTokScriptRequest(BaseModel):
    product_id: int
    content_type: str = "product_demo"  # product_demo, before_after, tips, story, trending
    trending_sound: Optional[str] = None


@app.post("/api/tiktok/generate-script")
async def generate_tiktok_script(request: TikTokScriptRequest):
    """Generate TikTok video script for a product"""
    from services.ai_service import get_ai_service
    from models.database import SessionLocal, Product
    
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == request.product_id).first()
    db.close()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    ai = get_ai_service()
    
    product_data = {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": product.selling_price,
        "category": "home organization",  # You can add category field to Product
        "supplier": product.supplier_name
    }
    
    script = await ai.generate_tiktok_script(
        product_data,
        content_type=request.content_type,
        trending_sound=request.trending_sound
    )
    
    return {
        "product_id": request.product_id,
        "product_title": product.title,
        "script": script
    }


@app.get("/api/tiktok/content-calendar")
async def get_tiktok_calendar(days: int = 30, store_id: Optional[int] = None):
    """Generate TikTok content calendar"""
    from services.ai_service import get_ai_service
    from models.database import SessionLocal, Product
    
    db = SessionLocal()
    query = db.query(Product).filter(Product.status == "active")
    if store_id:
        query = query.filter(Product.store_id == store_id)
    products = query.limit(10).all()
    db.close()
    
    products_data = [
        {
            "id": p.id,
            "title": p.title,
            "price": p.selling_price,
            "description": p.description[:100] if p.description else ""
        }
        for p in products
    ]
    
    ai = get_ai_service()
    calendar = await ai.generate_tiktok_calendar(products_data, days=days)
    
    return {
        "days": days,
        "products_available": len(products_data),
        "calendar": calendar
    }


@app.get("/api/tiktok/trending-hashtags")
async def get_trending_hashtags(niche: str = "home organization"):
    """Get trending hashtags for your niche"""
    # These are current trending hashtags for home/organization niche
    # In production, you could scrape or use an API for real-time trends
    hashtags = {
        "always_trending": [
            "#homeorganization",
            "#organization", 
            "#organizing",
            "#homeorganizing",
            "#organizationhacks",
            "#declutter",
            "#tidyingup",
            "#cleanhome",
            "#organizedlife"
        ],
        "trending_now": [
            "#satisfying",
            "#asmr",
            "#restock",
            "#cleantok",
            "#organizationtiktok",
            "#homehacks",
            "#smallbusiness",
            "#tiktokmademebuyit"
        ],
        "niche_specific": {
            "home organization": [
                "#kitchenorganization",
                "#bathroomorganization", 
                "#bedroomorganization",
                "#closetorganization",
                "#drawerorganization",
                "#fridgeorganization",
                "#pantryorganization",
                "#under Sink",
                "#deskorganization"
            ],
            "cleaning": [
                "#cleaninghacks",
                "#cleaningtips",
                "#speedclean",
                "#deepclean",
                "#cleanwithme"
            ]
        }
    }
    
    return {
        "niche": niche,
        "hashtags": hashtags,
        "recommended_mix": {
            "broad_reach": ["#homeorganization", "#organization", "#satisfying"],
            "niche_targeted": ["#kitchenorganization", "#organizing"],
            "trending": ["#tiktokmademebuyit", "#restock"],
            "branded": ["#coaihome"]  # Replace with your brand
        },
        "usage_tips": [
            "Use 5-7 hashtags per video",
            "Mix broad + niche + trending",
            "Add 1 branded hashtag",
            "Put in caption, not comments"
        ]
    }


# ============ API Routes - Store Redesign ============

class RedesignRequest(BaseModel):
    store_id: int
    new_theme: Optional[str] = None  # minimal, bold, luxury, cozy, modern
    goals: List[str] = []  # higher_conversion, better_branding, modern_look


@app.post("/api/store/redesign")
async def generate_store_redesign(request: RedesignRequest):
    """Generate AI store redesign recommendations"""
    from services.ai_service import get_ai_service
    from models.database import SessionLocal, Store, Product
    
    db = SessionLocal()
    store = db.query(Store).filter(Store.id == request.store_id).first()
    products = db.query(Product).filter(
        Product.store_id == request.store_id,
        Product.status == "active"
    ).limit(10).all()
    db.close()
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    ai = get_ai_service()
    
    current_store_data = {
        "store_id": store.id,
        "brand_name": store.brand_name,
        "niche": store.niche,
        "current_colors": {
            "primary": store.primary_color,
            "secondary": store.secondary_color
        },
        "brand_tone": store.brand_tone,
        "product_count": len(products),
        "top_products": [
            {"title": p.title, "price": p.selling_price} for p in products[:5]
        ]
    }
    
    redesign = await ai.generate_store_redesign(
        current_store_data,
        new_theme=request.new_theme
    )
    
    return {
        "store_id": request.store_id,
        "current_brand": store.brand_name,
        "redesign": redesign
    }


@app.post("/api/store/update-branding")
async def update_store_branding(store_id: int, branding: Dict[str, Any]):
    """Update store branding colors and tone"""
    from automation.store_builder import get_store_builder
    
    builder = get_store_builder()
    result = await builder.update_store_branding(store_id, branding)
    return result


# ============ API Routes - System ============

@app.get("/api/scheduler/jobs")
async def get_scheduler_jobs():
    """Get scheduled job status"""
    try:
        from automation.scheduler import get_scheduler
        scheduler = get_scheduler()
        return {"jobs": scheduler.get_jobs()}
    except Exception as e:
        return {"jobs": [], "warning": f"Scheduler unavailable: {e}"}


@app.get("/api/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        from models.database import SessionLocal, Product, PriceChange, OrderException, Store
        db = SessionLocal()
        
        stats = {
            "total_products": db.query(Product).count(),
            "active_products": db.query(Product).filter(Product.status == "active").count(),
            "pending_products": db.query(Product).filter(Product.status == "pending_approval").count(),
            "pending_price_changes": db.query(PriceChange).filter(PriceChange.status == "pending").count(),
            "open_exceptions": db.query(OrderException).filter(OrderException.status == "open").count(),
            "total_stores": db.query(Store).count()
        }
        
        db.close()
        return stats
    except Exception as e:
        # Return empty stats if database not ready
        return {
            "total_products": 0,
            "active_products": 0,
            "pending_products": 0,
            "pending_price_changes": 0,
            "open_exceptions": 0,
            "total_stores": 0,
            "error": str(e)
        }


@app.get("/health")
async def health_check():
    """Health check endpoint with database verification"""
    import os
    
    # Check environment
    shop_url = os.getenv("SHOPIFY_SHOP_URL", "")
    has_credentials = bool(os.getenv("SHOPIFY_ACCESS_TOKEN") or 
                          (os.getenv("SHOPIFY_API_KEY") and os.getenv("SHOPIFY_API_SECRET")))
    
    # Check database
    db_status = "ok"
    try:
        from models.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "version": "1.0.0",
        "database": db_status,
        "shopify_configured": bool(shop_url),
        "shopify_credentials": has_credentials,
        "mode": "FULL" if has_credentials else "SETUP_REQUIRED"
    }


# ============ NEW: Full Automation Routes (NO AutoDS API Needed) ============

@app.post("/api/full-automation/setup")
async def full_automation_setup():
    """
    Complete setup for fully automated operation
    No AutoDS API required - uses browser automation instead
    """
    from automation.full_automation import get_full_automation
    auto = get_full_automation()
    result = await auto.run_full_setup()
    return result


@app.post("/api/full-automation/start")
async def start_full_automation():
    """
    Start the 24/7 automation scheduler
    Runs: product research, pricing, inventory sync, content creation
    """
    from automation.full_automation import get_full_automation
    import threading
    
    auto = get_full_automation()
    
    # Run scheduler in background thread
    def run_scheduler():
        asyncio.run(auto.start_scheduler())
    
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    
    return {
        "status": "started",
        "message": "Full automation scheduler running in background",
        "tasks": [
            "Daily product research at 09:00",
            "Daily product import at 10:00",
            "Daily pricing optimization at 14:00",
            "Daily TikTok content at 20:00",
            "Hourly inventory sync",
            "Order monitoring every 2 hours"
        ]
    }


@app.get("/api/full-automation/status")
async def get_automation_status():
    """Get current automation status"""
    from automation.full_automation import get_full_automation
    auto = get_full_automation()
    return auto.get_status()


@app.post("/api/full-automation/run-now")
async def run_all_automation_now():
    """Run all automation tasks immediately (for testing)"""
    from automation.full_automation import get_full_automation
    auto = get_full_automation()
    result = await auto.run_all_now()
    return result


# ============ NEW: TikTok Content Engine Routes ============

@app.post("/api/tiktok/generate-content")
async def generate_tiktok_content(store_id: Optional[int] = None):
    """
    Generate complete TikTok content calendar for all products
    Creates scripts, hooks, CTAs, and hashtags
    """
    try:
        from automation.tiktok_content_engine import get_tiktok_content_engine
        engine = get_tiktok_content_engine()
        
        result = await engine.auto_create_content_for_store()
        return result
    except Exception as e:
        import traceback
        print(f"Error generating TikTok content: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "message": "Failed to generate content. Check server logs.",
            "products": 0,
            "content_pieces": 0
        }


@app.post("/api/tiktok/product-script")
async def generate_product_script(product_id: int, content_type: str = "product_demo"):
    """Generate a TikTok script for a specific product"""
    from automation.tiktok_content_engine import get_tiktok_content_engine
    from models.database import SessionLocal, Product
    
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == product_id).first()
    db.close()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    engine = get_tiktok_content_engine()
    
    product_data = {
        "title": product.title,
        "price": f"${product.selling_price}",
        "description": product.description or ""
    }
    
    script = await engine.generate_product_script(product_data, content_type)
    return {
        "product_id": product_id,
        "product_title": product.title,
        "content_type": content_type,
        "script": script
    }


@app.get("/api/tiktok/export-calendar")
async def export_content_calendar():
    """Export the content calendar to CSV"""
    from automation.tiktok_content_engine import get_tiktok_content_engine
    engine = get_tiktok_content_engine()
    engine.export_calendar_to_csv()
    return {"message": "Content calendar exported to content_calendar.csv"}


# ============ NEW: No-API Product Research Routes ============

@app.post("/api/research/no-api")
async def research_products_no_api(niche: str = "home organization", limit: int = 20):
    """
    Research trending products WITHOUT AutoDS API
    Uses web scraping + AI analysis
    """
    try:
        from automation.product_research_no_api import get_product_research_no_api
        research = get_product_research_no_api()
        
        products = await research.research_trending_products(niche, limit)
        
        return {
            "niche": niche,
            "products_found": len(products),
            "products": [
                {
                    "title": p.title,
                    "supplier": p.supplier,
                    "cost_price": p.cost_price,
                    "suggested_price": p.suggested_price,
                    "profit_margin": round((p.suggested_price - p.cost_price) / p.suggested_price * 100, 1),
                    "shipping_days": p.shipping_days,
                    "rating": p.rating,
                    "order_count": p.order_count,
                    "ai_score": p.ai_score,
                    "ai_recommendation": p.ai_analysis.get("recommendation") if p.ai_analysis else None,
                    "supplier_url": p.supplier_url
                }
                for p in products
            ]
        }
    except Exception as e:
        return {"error": str(e), "products_found": 0, "products": []}


@app.post("/api/research/export-report")
async def export_research_report(niche: str = "home organization"):
    """Export product research report to JSON"""
    from automation.product_research_no_api import get_product_research_no_api
    research = get_product_research_no_api()
    
    products = await research.research_trending_products(niche)
    filename = research.export_research_report(products)
    
    return {
        "message": "Research report exported",
        "filename": filename,
        "products_researched": len(products)
    }


@app.post("/api/research/analyze-competitor")
async def analyze_competitor_store(store_url: str):
    """
    Analyze a competitor's Shopify store for product ideas
    Note: Only analyzes publicly available data
    """
    from automation.product_research_no_api import get_product_research_no_api
    research = get_product_research_no_api()
    
    result = await research.analyze_competitor_store(store_url)
    return result


# ============ NEW: AutoDS Browser Automation Routes ============

@app.post("/api/autods/browser-login")
async def autods_browser_login(headless: bool = False):
    """
    Login to AutoDS using browser automation (no API needed)
    May require manual 2FA completion
    """
    from api_clients.autods_browser_client import get_browser_client
    
    try:
        client = await get_browser_client()
        await client.start(headless=headless)
        success = await client.login()
        
        if success:
            return {
                "status": "success",
                "message": "Logged into AutoDS via browser",
                "note": "Browser automation is now ready"
            }
        else:
            return {
                "status": "manual_intervention_required",
                "message": "Please complete 2FA in the browser window",
                "instruction": "Complete login manually, then browser automation will be available"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/autods/import-product")
async def import_product_browser(supplier_url: str, title: str, price: float):
    """
    Import a product using browser automation
    Works without AutoDS API!
    """
    from api_clients.autods_browser_client import get_browser_client
    
    client = await get_browser_client()
    
    if not client.logged_in:
        raise HTTPException(status_code=400, detail="Not logged in. Call /api/autods/browser-login first")
    
    result = await client.import_product_from_url(
        supplier_url=supplier_url,
        product_data={"title": title, "price": price}
    )
    
    return result


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.system.debug,
        log_level=settings.system.log_level.lower()
    )

