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
            "errors": []
        }
        
        try:
            # Step 1: Trigger AutoDS AI Store Builder
            print(f"🏗️  Starting AI Store Builder for: {store_spec['brand_name']}")
            builder_response = await self.autods.create_ai_store(store_spec)
            result["steps_completed"].append("autods_store_builder_triggered")
            result["autods_job_id"] = builder_response.get("job_id")
            
            # Step 2: Poll for completion (in production, use webhook)
            store_data = await self._wait_for_store_builder(
                builder_response.get("job_id")
            )
            result["steps_completed"].append("store_builder_completed")
            result["shopify_domain"] = store_data.get("shopify_domain")
            
            # Step 3: Generate additional AI content
            print("✍️  Generating store content...")
            store_content = await self.ai.generate_store_content(store_spec)
            result["steps_completed"].append("content_generated")
            
            # Step 4: Update Shopify pages with AI content
            await self._update_store_pages(store_data.get("shopify_domain"), store_content)
            result["steps_completed"].append("pages_updated")
            
            # Step 5: Save to database
            db = SessionLocal()
            store = Store(
                shopify_store_id=store_data.get("shopify_store_id"),
                shopify_domain=store_data.get("shopify_domain"),
                brand_name=store_spec["brand_name"],
                niche=store_spec["niche"],
                target_country=store_spec.get("target_country", "US"),
                currency="USD",
                primary_color=store_spec.get("primary_color", "#000000"),
                secondary_color=store_spec.get("secondary_color", "#ffffff"),
                brand_tone=store_spec.get("brand_tone", "professional"),
                autods_connected=True,
                auto_fulfillment_enabled=True
            )
            db.add(store)
            db.commit()
            result["store_id"] = store.id
            db.close()
            
            result["status"] = "completed"
            print(f"✅ Store creation completed: {result['shopify_domain']}")
            
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
