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
async def landing(request: Request):
    """Landing page for SaaS promotion"""
    return templates.TemplateResponse("landing.html", {"request": request})


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
    from automation.fulfillment_monitor import get_fulfillment_monitor
    monitor = get_fulfillment_monitor()
    result = await monitor.run_inventory_sync(store_id)
    return result


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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


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

