"""
Phase 2: AI Product Research and Catalog Management
Automated product discovery, analysis, and import
"""
import asyncio
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta

from api_clients.autods_client import get_autods_client
from api_clients.shopify_client import get_shopify_client
from services.ai_service import get_ai_service
from config.settings import settings
from models.database import SessionLocal, Product, ProductResearchJob, ProductStatus, Store
from automation.utils import _safe_print


class ProductResearchAutomation:
    """Automates product research and import workflows"""
    
    def __init__(self):
        self.autods = get_autods_client()
        self.shopify = get_shopify_client()
        self.ai = get_ai_service()

    async def _run_no_api_research(self, store_id: int, niche: str, limit: int = 10) -> Dict:
        """Fallback research path that does not require supplier API access."""
        _safe_print(f"🕵️  Jake Engine: Falling back to No-API research for: {niche}")
        from automation.product_research_no_api import get_product_research_no_api
        research_engine = get_product_research_no_api()
        opportunities = await research_engine.research_trending_products(niche, limit=limit)

        for op in opportunities:
            p_data = {
                "title": op.title,
                "description": op.description,
                "cost_price": op.cost_price,
                "supplier_id": "aliexpress_" + str(random.randint(1000, 9999)),
                "supplier_name": op.supplier,
                "supplier_rating": op.rating,
                "shipping_days": op.shipping_days,
                "source_url": op.supplier_url,
                "images": op.images
            }
            analysis = op.ai_analysis or {
                "confidence": op.ai_score / 100,
                "suggested_price": op.suggested_price
            }
            await self._queue_for_approval(store_id, [(p_data, analysis)])

        return {
            "status": "completed",
            "message": f"Found {len(opportunities)} products in {niche}. Go to 'Products' to approve!",
            "products_found": len(opportunities),
            "products_selected": len(opportunities)
        }
    
    async def run_research_job(self, store_id: int, 
                               niche: Optional[str] = None) -> Dict:
        """
        Run a complete product research job
        
        SHOPIFY-ONLY MODE: Returns instructions for manual research
        FULL MODE: Automated research via AutoDS
        """
        db = SessionLocal()
        store = db.query(Store).filter(Store.id == store_id).first()
        
        if not store:
            db.close()
            return {"status": "error", "message": "Store not found"}
        
        niche = niche or store.niche
        
        # Check if supplier API automation is available
        if self.autods.shopify_mode:
            db.close()
            return await self._run_no_api_research(store_id, niche, limit=10)
        
        # Check if CJ mode is active
        is_cj_mode = self.autods.provider == "cj" and not self.autods.shopify_mode
        if is_cj_mode:
            _safe_print(f"🚀 Running product research with CJ Dropshipping API for niche: {niche}")
        
        # Create job record (only for full mode)
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
            _safe_print(f"🔍 Researching trending products in: {niche}")
            trending = await self.autods.get_trending_products(
                niche=niche,
                limit=50,
                country=store.target_country
            )
            if trending.get("error"):
                supplier_error = str(trending.get("error"))
                _safe_print(f"⚠️  Supplier API unavailable: {supplier_error}")
                fallback = await self._run_no_api_research(store_id, niche, limit=10)
                result["status"] = fallback.get("status", "completed")
                result["products_found"] = fallback.get("products_found", 0)
                result["products_selected"] = fallback.get("products_selected", 0)
                result["products_imported"] = 0
                result["errors"].append(f"CJ fallback used: {supplier_error}")

                job.products_found = result["products_found"]
                job.products_selected = result["products_selected"]
                job.products_imported = 0
                job.status = result["status"]
                job.error_message = f"CJ fallback used: {supplier_error}"
                job.completed_at = datetime.utcnow()
                db.commit()
                db.close()
                return result

            products = trending.get("products", [])
            result["products_found"] = len(products)
            job.products_found = len(products)
            db.commit()
            
            # Step 2: Apply constraints and get detailed data
            qualified_products = await self._filter_by_constraints(products)
            
            # Step 3: AI analysis
            _safe_print(f"🤖 Analyzing {len(qualified_products)} products...")
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
                _safe_print(f"⏳ {len(selected)} products queued for approval")
                await self._queue_for_approval(store_id, selected)
                result["status"] = "pending_approval"
            else:
                _safe_print(f"📦 Importing {len(selected)} products...")
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
            _safe_print(f"❌ Research job failed: {e}")
        
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
                selling_price=analysis.get("suggested_price", 0), # Store the calculated price
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
        """Import products to Shopify and establish mapping"""
        from models.database import GlobalVariantMapping, VariantMap
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
                    "source_vid": product_data.get("vid"),
                    "source_url": product_data.get("source_url"),
                    "title": content.get("title", product_data.get("title")),
                    "description": content.get("description_html", product_data.get("description")),
                    "cost_price": product_data.get("cost_price"),
                    "suggested_price": analysis.get("suggested_price", 0),
                    "tags": content.get("tags", []),
                    "image_urls": product_data.get("images", [])
                }
                
                # Trigger Import
                result = await self.autods.import_product(
                    import_data,
                    store.shopify_domain
                )
                
                if result.get("success"):
                    sh_prod_id = result.get("shopify_product_id")
                    sh_var_id = result.get("shopify_variant_id")
                    cj_var_id = result.get("supplier_variant_id") or product_data.get("vid")
                    
                    # Save Product Record
                    product = Product(
                        store_id=store_id,
                        shopify_product_id=str(sh_prod_id),
                        shopify_variant_id=str(sh_var_id) if sh_var_id else None,
                        autods_product_id=result.get("autods_product_id"),
                        title=import_data["title"],
                        description=import_data["description"],
                        cost_price=import_data["cost_price"],
                        selling_price=import_data["suggested_price"],
                        supplier_id=product_data.get("supplier_id"),
                        supplier_name=product_data.get("supplier_name"),
                        status=ProductStatus.ACTIVE
                    )
                    db.add(product)
                    
                    # Store critical mapping for fulfillment automation
                    if sh_var_id and cj_var_id:
                        sku = f"COAI-{product_data.get('id')}"
                        
                        # 1. Backwards compatibility mapping
                        v_map = VariantMap(
                            store_id=store_id,
                            shopify_variant_id=str(sh_var_id),
                            cj_variant_id=str(cj_var_id),
                            sku=sku
                        )
                        db.add(v_map)
                        
                        # 2. Modern 'Nervous System' Cluster Mapping
                        g_map = GlobalVariantMapping(
                            master_sku=sku,
                            cj_product_id=str(product_data.get("id")),
                            cj_variant_id=str(cj_var_id),
                            shopify_product_id=str(sh_prod_id),
                            shopify_variant_id=str(sh_var_id),
                            active=True
                        )
                        db.add(g_map)

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


def get_product_research() -> ProductResearchAutomation:
    return ProductResearchAutomation()
