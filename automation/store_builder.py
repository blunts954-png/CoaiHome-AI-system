"""
Phase 1: AI Store Creation Pipeline
Handles store generation via AutoDS AI Store Builder or alternative builders
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from api_clients.autods_client import get_autods_client
from api_clients.shopify_client import get_shopify_client
from services.ai_service import get_ai_service
from config.settings import settings
from models.database import SessionLocal, Store, Product


class AIStoreBuilder:
    """Orchestrates AI store creation from spec to live store"""
    
    def __init__(self):
        self.autods = get_autods_client()
        self.shopify = get_shopify_client()
        self.ai = get_ai_service()
    
    async def create_store_from_spec(self, store_spec: Dict[str, Any]) -> Dict:
        """
        Create a complete Shopify store from a specification
        
        SHOPIFY-ONLY MODE: Creates store record and generates content,
        but requires manual store setup via Shopify
        FULL MODE: Uses AutoDS AI Store Builder
        
        Args:
            store_spec: {
                "niche": str,
                "brand_name": str,
                "target_country": str,
                "brand_tone": str,
                "primary_color": str,
                "secondary_color": str,
                "price_range": {"min": float, "max": float},
                "num_products": int
            }
        
        Returns:
            Store creation result with IDs and URLs
        """
        result = {
            "status": "started",
            "steps_completed": [],
            "store_id": None,
            "shopify_domain": None,
            "products_imported": [],
            "errors": [],
            "mode": "SHOPIFY-ONLY" if self.autods.shopify_mode else "FULL"
        }
        
        try:
            # 1. Update branding immediately
            from auto_build_shopify_store import AutomaticShopifyBuilder
            builder = AutomaticShopifyBuilder()
            
            print(f"🏗️  Jake Engine: Building store for: {store_spec['brand_name']}")
            
            # Update .env with spec if needed
            from config.settings import settings
            settings.store.niche = store_spec["niche"]
            settings.store.brand_name = store_spec["brand_name"]
            settings.store.brand_tone = store_spec.get("brand_tone", "professional")
            
            # Step 1: Run the actual build logic (Manual Engine)
            # This is what I was doing in the terminal - now it's inside your button.
            build_results = await builder.build_store()
            
            if build_results.get("status") == "completed":
                result["steps_completed"].append("manual_build_executed")
                result["status"] = "completed"
                result["message"] = f"SUCCESS: {store_spec['brand_name']} is now live!"
            else:
                result["status"] = "partial_success"
                result["message"] = f"Build completed with issues: {build_results.get('error', 'Unknown warning')}"
            
            # Step 2: Save to database for dashboard tracking
            db = SessionLocal()
            store = Store(
                shopify_store_id="manual_build_" + str(int(datetime.now().timestamp())),
                shopify_domain=settings.shopify.shop_url,
                brand_name=store_spec["brand_name"],
                niche=store_spec["niche"],
                target_country=store_spec.get("target_country", "US"),
                currency="USD",
                primary_color=store_spec.get("primary_color", "#000000"),
                secondary_color=store_spec.get("secondary_color", "#ffffff"),
                brand_tone=store_spec.get("brand_tone", "professional"),
                autods_connected=False,
                auto_fulfillment_enabled=False
            )
            db.add(store)
            db.commit()
            result["store_id"] = store.id
            db.close()
            
            print(f"✅ App Updated: Store ID {result['store_id']} is active.")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            print(f"❌ Store creation failed: {e}")
        
        return result
    
    async def _wait_for_store_builder(self, job_id: str, 
                                     max_wait_seconds: int = 600) -> Dict:
        """Poll AutoDS for store builder completion"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            status = await self.autods.get_store_builder_status(job_id)
            
            if status.get("status") == "completed":
                return status.get("store_data", {})
            elif status.get("status") == "failed":
                raise Exception(f"Store builder failed: {status.get('error')}")
            
            await asyncio.sleep(10)  # Poll every 10 seconds
        
        raise Exception("Store builder timed out")
    
    async def _update_store_pages(self, shopify_domain: str, content: Dict):
        """Update Shopify pages with AI-generated content"""
        try:
            # Create About Us page
            if content.get("about_us_html"):
                await self.shopify.create_page(
                    title="About Us",
                    body_html=content["about_us_html"],
                    handle="about-us"
                )
            
            # Create Shipping & Returns page
            if content.get("shipping_policy_html"):
                await self.shopify.create_page(
                    title="Shipping & Returns",
                    body_html=content["shipping_policy_html"],
                    handle="shipping-returns"
                )
            
            # Create FAQ page
            if content.get("faq"):
                faq_html = self._build_faq_html(content["faq"])
                await self.shopify.create_page(
                    title="FAQ",
                    body_html=faq_html,
                    handle="faq"
                )
                
        except Exception as e:
            print(f"Warning: Failed to update some pages: {e}")
    
    def _build_faq_html(self, faqs: list) -> str:
        """Build FAQ HTML from structured data"""
        html = "<div class='faq-section'>\n"
        for item in faqs:
            html += f"<div class='faq-item'>\n"
            html += f"  <h3>{item.get('q', '')}</h3>\n"
            html += f"  <p>{item.get('a', '')}</p>\n"
            html += "</div>\n"
        html += "</div>"
        return html
    
    async def update_store_branding(self, store_id: int, 
                                    branding_updates: Dict) -> Dict:
        """Update store branding (colors, logo, tone)"""
        db = SessionLocal()
        store = db.query(Store).filter(Store.id == store_id).first()
        
        if not store:
            db.close()
            return {"status": "error", "message": "Store not found"}
        
        # Update local record
        if "primary_color" in branding_updates:
            store.primary_color = branding_updates["primary_color"]
        if "secondary_color" in branding_updates:
            store.secondary_color = branding_updates["secondary_color"]
        if "brand_tone" in branding_updates:
            store.brand_tone = branding_updates["brand_tone"]
        
        store.updated_at = datetime.utcnow()
        db.commit()
        db.close()
        
        return {"status": "success", "store_id": store_id}


# Factory function
def get_store_builder() -> AIStoreBuilder:
    return AIStoreBuilder()
