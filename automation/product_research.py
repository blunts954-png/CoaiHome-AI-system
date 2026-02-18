"""
Phase 2: AI Product Research and Catalog Management
Automated product discovery, analysis, and import
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from api_clients.autods_client import get_autods_client
from api_clients.shopify_client import get_shopify_client
from services.ai_service import get_ai_service
from config.settings import settings
from models.database import SessionLocal, Product, ProductResearchJob, ProductStatus


class ProductResearchAutomation:
    """Automates product research and import workflows"""
    
    def __init__(self):
        self.autods = get_autods_client()
        self.shopify = get_shopify_client()
        self.ai = get_ai_service()
    
    async def run_research_job(self, store_id: int, 
                               niche: Optional[str] = None) -> Dict:
        """
        Run a complete product research job
        
        Flow:
        1. Search for trending products
        2. Filter by constraints
        3. AI analysis of opportunities
        4. Select best products
        5. Import approved products
        """
        db = SessionLocal()
        store = db.query(Store).filter(Store.id == store_id).first()
        
        if not store:
            db.close()
            return {"status": "error", "message": "Store not found"}
        
        niche = niche or store.niche
        
        # Create job record
        job = ProductResearchJob(
            store_id=store_id,
            niche=niche,
            min_margin=settings.ai.min_profit_margin,
            max_shipping_days=settings.ai.max_shipping_days,
            min_rating=settings.ai.min_product_rating,
            status="running"
        )
        db.add(job)
        db.commit()
        
        result = {
            "job_id": job.id,
            "status": "running",
            "products_found": 0,
            "products_selected": 0,
            "products_imported": 0,
            "errors": []
        }
        
        try:
            # Step 1: Get trending products
            print(f"🔍 Researching trending products in: {niche}")
            trending = await self.autods.get_trending_products(
                niche=niche,
                limit=50,
                country=store.target_country
            )
            products = trending.get("products", [])
            result["products_found"] = len(products)
            job.products_found = len(products)
            db.commit()
            
            # Step 2: Apply constraints and get detailed data
            qualified_products = await self._filter_by_constraints(products)
            
            # Step 3: AI analysis
            print(f"🤖 Analyzing {len(qualified_products)} products...")
            analysis_tasks = [
                self._analyze_product(p, store) for p in qualified_products
            ]
            analyses = await asyncio.gather(*analysis_tasks)
            
            # Step 4: Select best products
            approved_products = [
                (p, a) for p, a in zip(qualified_products, analyses)
                if a.get("should_import") and a.get("confidence", 0) > 0.7
            ]
            
            # Sort by confidence and take top N
            approved_products.sort(key=lambda x: x[1].get("confidence", 0), reverse=True)
            max_imports = settings.ai.max_products_per_day
            selected = approved_products[:max_imports]
            
            result["products_selected"] = len(selected)
            job.products_selected = len(selected)
            db.commit()
            
            # Step 5: Import products (or queue for approval)
            if settings.system.require_approval_for_import:
                print(f"⏳ {len(selected)} products queued for approval")
                await self._queue_for_approval(store_id, selected)
                result["status"] = "pending_approval"
            else:
                print(f"📦 Importing {len(selected)} products...")
                imported = await self._import_products(store_id, store, selected)
                result["products_imported"] = imported
                job.products_imported = imported
                result["status"] = "completed"
            
            job.status = result["status"]
            job.completed_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            print(f"❌ Research job failed: {e}")
        
        db.close()
        return result
    
    async def _filter_by_constraints(self, products: List[Dict]) -> List[Dict]:
        """Filter products by business constraints"""
        qualified = []
        
        for product in products:
            # Check shipping time
            shipping_days = product.get("shipping_days", 999)
            if shipping_days > settings.ai.max_shipping_days:
                continue
            
            # Check supplier rating
            rating = product.get("supplier_rating", 0)
            if rating < settings.ai.min_product_rating:
                continue
            
            # Check potential margin
            cost = product.get("cost_price", 0)
            suggested_price = cost * settings.store.base_markup
            margin = ((suggested_price - cost) / suggested_price) * 100
            
            if margin < settings.ai.min_profit_margin:
                continue
            
            # Check price range
            if suggested_price < settings.store.min_price:
                continue
            if suggested_price > settings.store.max_price:
                continue
            
            qualified.append(product)
        
        return qualified
    
    async def _analyze_product(self, product: Dict, store) -> Dict:
        """Run AI analysis on a single product"""
        constraints = {
            "min_margin_percent": settings.ai.min_profit_margin,
            "max_shipping_days": settings.ai.max_shipping_days,
            "min_rating": settings.ai.min_product_rating,
            "target_country": store.target_country,
            "niche": store.niche
        }
        
        return await self.ai.analyze_product_opportunity(product, constraints)
    
    async def _queue_for_approval(self, store_id: int, 
                                   products: List[tuple]):
        """Queue products for manual approval"""
        db = SessionLocal()
        
        for product_data, analysis in products:
            product = Product(
                store_id=store_id,
                title=product_data.get("title"),
                description=product_data.get("description"),
                cost_price=product_data.get("cost_price", 0),
                suggested_price=analysis.get("suggested_price", 0),
                supplier_id=product_data.get("supplier_id"),
                supplier_name=product_data.get("supplier_name"),
                supplier_rating=product_data.get("supplier_rating"),
                shipping_days=product_data.get("shipping_days"),
                ai_import_confidence=analysis.get("confidence", 0),
                ai_research_data={
                    "source_data": product_data,
                    "analysis": analysis
                },
                status=ProductStatus.PENDING_APPROVAL
            )
            db.add(product)
        
        db.commit()
        db.close()
    
    async def _import_products(self, store_id: int, store, 
                               products: List[tuple]) -> int:
        """Import products to Shopify via AutoDS"""
        imported_count = 0
        db = SessionLocal()
        
        for product_data, analysis in products:
            try:
                # Generate optimized content
                content = await self.ai.generate_product_description(
                    product_data,
                    brand_tone=store.brand_tone
                )
                
                # Prepare import data
                import_data = {
                    "source_id": product_data.get("id"),
                    "source_url": product_data.get("source_url"),
                    "title": content.get("title", product_data.get("title")),
                    "description": content.get("description_html", product_data.get("description")),
                    "cost_price": product_data.get("cost_price"),
                    "markup": analysis.get("suggested_markup", settings.store.base_markup),
                    "tags": content.get("tags", []),
                    "image_urls": product_data.get("images", [])
                }
                
                # Trigger AutoDS import
                result = await self.autods.import_product(
                    import_data,
                    store.shopify_domain
                )
                
                if result.get("success"):
                    # Save to database
                    product = Product(
                        store_id=store_id,
                        shopify_product_id=result.get("shopify_product_id"),
                        autods_product_id=result.get("autods_product_id"),
                        title=import_data["title"],
                        description=import_data["description"],
                        cost_price=import_data["cost_price"],
                        selling_price=analysis.get("suggested_price", 0),
                        supplier_id=product_data.get("supplier_id"),
                        supplier_name=product_data.get("supplier_name"),
                        supplier_rating=product_data.get("supplier_rating"),
                        shipping_days=product_data.get("shipping_days"),
                        ai_import_confidence=analysis.get("confidence", 0),
                        ai_research_data={
                            "source_data": product_data,
                            "analysis": analysis
                        },
                        status=ProductStatus.ACTIVE
                    )
                    db.add(product)
                    imported_count += 1
                    
            except Exception as e:
                print(f"Failed to import product {product_data.get('id')}: {e}")
        
        db.commit()
        db.close()
        return imported_count
    
    async def approve_pending_product(self, product_id: int) -> Dict:
        """Manually approve a pending product for import"""
        db = SessionLocal()
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            db.close()
            return {"status": "error", "message": "Product not found"}
        
        if product.status != ProductStatus.PENDING_APPROVAL:
            db.close()
            return {"status": "error", "message": "Product not pending approval"}
        
        try:
            # Get store info
            store = db.query(Store).filter(Store.id == product.store_id).first()
            
            # Import the product
            research_data = product.ai_research_data or {}
            source_data = research_data.get("source_data", {})
            analysis = research_data.get("analysis", {})
            
            content = await self.ai.generate_product_description(
                source_data,
                brand_tone=store.brand_tone
            )
            
            import_data = {
                "source_id": source_data.get("id"),
                "source_url": source_data.get("source_url"),
                "title": content.get("title", product.title),
                "description": content.get("description_html", product.description),
                "cost_price": product.cost_price,
                "markup": analysis.get("suggested_markup", settings.store.base_markup),
                "tags": content.get("tags", [])
            }
            
            result = await self.autods.import_product(import_data, store.shopify_domain)
            
            if result.get("success"):
                product.shopify_product_id = result.get("shopify_product_id")
                product.autods_product_id = result.get("autods_product_id")
                product.status = ProductStatus.ACTIVE
                db.commit()
                db.close()
                return {"status": "success", "product_id": product_id}
            else:
                db.close()
                return {"status": "error", "message": "Import failed"}
                
        except Exception as e:
            db.close()
            return {"status": "error", "message": str(e)}
    
    async def reject_pending_product(self, product_id: int, reason: str = "") -> Dict:
        """Reject a pending product"""
        db = SessionLocal()
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if product and product.status == ProductStatus.PENDING_APPROVAL:
            product.status = ProductStatus.REMOVED
            db.commit()
        
        db.close()
        return {"status": "success", "product_id": product_id}


from models.database import Store


def get_product_research() -> ProductResearchAutomation:
    return ProductResearchAutomation()
