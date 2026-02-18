"""
Phase 3.1: AI-Assisted Pricing and Profit Rules
Automated price optimization based on performance metrics
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from api_clients.autods_client import get_autods_client
from api_clients.shopify_client import get_shopify_client
from services.ai_service import get_ai_service
from config.settings import settings
from models.database import SessionLocal, Product, PriceChange, PriceChangeStatus


class PricingEngine:
    """AI-powered pricing optimization engine"""
    
    def __init__(self):
        self.autods = get_autods_client()
        self.shopify = get_shopify_client()
        self.ai = get_ai_service()
    
    async def run_pricing_optimization(self, store_id: Optional[int] = None,
                                       product_ids: Optional[List[int]] = None) -> Dict:
        """
        Run the complete pricing optimization workflow
        
        Flow:
        1. Fetch product performance data
        2. Get AI price suggestions
        3. Validate against constraints
        4. Queue for approval or apply directly
        5. Log all changes
        """
        db = SessionLocal()
        
        # Get products to optimize
        query = db.query(Product).filter(Product.status == "active")
        if store_id:
            query = query.filter(Product.store_id == store_id)
        if product_ids:
            query = query.filter(Product.id.in_(product_ids))
        
        products = query.all()
        db.close()
        
        if not products:
            return {"status": "no_products", "message": "No active products to optimize"}
        
        result = {
            "status": "started",
            "products_analyzed": len(products),
            "suggestions_generated": 0,
            "pending_approval": 0,
            "applied": 0,
            "rejected": 0,
            "errors": []
        }
        
        try:
            # Step 1: Gather performance data
            print(f"📊 Analyzing {len(products)} products for pricing...")
            product_data = await self._gather_product_data(products)
            
            # Step 2: Get AI optimization suggestions
            suggestions = await self.ai.optimize_prices(product_data)
            result["suggestions_generated"] = len(suggestions)
            
            # Step 3: Validate and process each suggestion
            for suggestion in suggestions:
                try:
                    await self._process_price_suggestion(suggestion, products)
                    
                    if settings.system.require_approval_for_price_changes:
                        result["pending_approval"] += 1
                    else:
                        result["applied"] += 1
                        
                except Exception as e:
                    result["errors"].append(f"Product {suggestion.get('product_id')}: {e}")
                    result["rejected"] += 1
            
            result["status"] = "completed"
            print(f"✅ Pricing optimization completed: {result['applied']} applied, {result['pending_approval']} pending")
            
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))
            print(f"❌ Pricing optimization failed: {e}")
        
        return result
    
    async def _gather_product_data(self, products: List[Product]) -> List[Dict]:
        """Gather performance data for products"""
        data = []
        
        for product in products:
            # Get analytics from AutoDS
            try:
                analytics = await self.autods.get_product_performance(
                    product.autods_product_id,
                    days=30
                )
            except:
                analytics = {}
            
            # Calculate conversion rate
            views = product.views or 0
            add_to_carts = product.add_to_carts or 0
            orders = product.orders or 0
            
            conversion_rate = (orders / views * 100) if views > 0 else 0
            cart_abandonment = ((add_to_carts - orders) / add_to_carts * 100) if add_to_carts > 0 else 0
            
            product_info = {
                "id": product.id,
                "shopify_id": product.shopify_product_id,
                "autods_id": product.autods_product_id,
                "title": product.title,
                "current_price": product.selling_price,
                "cost_price": product.cost_price,
                "current_margin": product.profit_margin_percent,
                "views": views,
                "add_to_carts": add_to_carts,
                "orders": orders,
                "revenue": product.revenue,
                "conversion_rate": conversion_rate,
                "cart_abandonment_rate": cart_abandonment,
                "refund_rate": product.refund_rate,
                "days_since_created": (datetime.utcnow() - product.created_at).days if product.created_at else 0,
                "autods_analytics": analytics
            }
            
            data.append(product_info)
        
        return data
    
    async def _process_price_suggestion(self, suggestion: Dict, 
                                        products: List[Product]):
        """Process a single price change suggestion"""
        db = SessionLocal()
        
        try:
            # Find the product
            product = next(
                (p for p in products if p.id == suggestion.get("product_id")),
                None
            )
            
            if not product:
                return
            
            # Validate constraints
            current_price = product.selling_price
            suggested_price = suggestion.get("suggested_price", current_price)
            
            # Check max price change
            change_percent = abs((suggested_price - current_price) / current_price * 100)
            if change_percent > settings.ai.max_price_change_percent:
                # Cap the change
                max_change = current_price * (settings.ai.max_price_change_percent / 100)
                if suggested_price > current_price:
                    suggested_price = current_price + max_change
                else:
                    suggested_price = current_price - max_change
            
            # Check minimum margin
            cost = product.cost_price
            new_margin = ((suggested_price - cost) / suggested_price) * 100
            if new_margin < settings.ai.min_profit_margin:
                # Adjust to maintain minimum margin
                min_price = cost / (1 - settings.ai.min_profit_margin / 100)
                suggested_price = max(suggested_price, min_price)
            
            # Round to .99
            suggested_price = int(suggested_price) + settings.store.price_rounding
            
            # Skip if no significant change
            if abs(suggested_price - current_price) < 0.5:
                return
            
            # Create price change record
            price_change = PriceChange(
                product_id=product.id,
                old_price=current_price,
                suggested_price=suggested_price,
                final_price=suggested_price if not settings.system.require_approval_for_price_changes else None,
                ai_reasoning=suggestion.get("reasoning", ""),
                confidence_score=suggestion.get("confidence", 0),
                conversion_rate=suggestion.get("conversion_rate"),
                status=PriceChangeStatus.PENDING if settings.system.require_approval_for_price_changes else PriceChangeStatus.APPLIED
            )
            
            db.add(price_change)
            db.commit()
            
            # Apply immediately if no approval required
            if not settings.system.require_approval_for_price_changes:
                await self._apply_price_change(price_change, product)
                price_change.status = PriceChangeStatus.APPLIED
                price_change.applied_at = datetime.utcnow()
                db.commit()
            
        finally:
            db.close()
    
    async def _apply_price_change(self, price_change: PriceChange, 
                                   product: Product):
        """Apply a price change to Shopify and AutoDS"""
        try:
            # Update in Shopify
            if product.shopify_product_id and product.shopify_variant_id:
                await self.shopify.update_product_price(
                    product.shopify_product_id,
                    product.shopify_variant_id,
                    price_change.final_price
                )
            
            # Update in AutoDS
            if product.autods_product_id:
                await self.autods.apply_price_changes([{
                    "product_id": product.autods_product_id,
                    "new_price": price_change.final_price,
                    "reason": price_change.ai_reasoning
                }])
            
            # Update local record
            product.selling_price = price_change.final_price
            product.profit_margin_percent = (
                (price_change.final_price - product.cost_price) / price_change.final_price * 100
            )
            product.updated_at = datetime.utcnow()
            
        except Exception as e:
            print(f"Failed to apply price change for product {product.id}: {e}")
            raise
    
    async def approve_price_change(self, price_change_id: int) -> Dict:
        """Manually approve a pending price change"""
        db = SessionLocal()
        
        try:
            price_change = db.query(PriceChange).filter(
                PriceChange.id == price_change_id
            ).first()
            
            if not price_change:
                return {"status": "error", "message": "Price change not found"}
            
            if price_change.status != PriceChangeStatus.PENDING:
                return {"status": "error", "message": "Price change not pending"}
            
            product = db.query(Product).filter(
                Product.id == price_change.product_id
            ).first()
            
            price_change.final_price = price_change.suggested_price
            await self._apply_price_change(price_change, product)
            
            price_change.status = PriceChangeStatus.APPLIED
            price_change.approved_at = datetime.utcnow()
            db.commit()
            
            return {"status": "success", "price_change_id": price_change_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
    
    async def reject_price_change(self, price_change_id: int) -> Dict:
        """Reject a pending price change"""
        db = SessionLocal()
        
        price_change = db.query(PriceChange).filter(
            PriceChange.id == price_change_id
        ).first()
        
        if price_change and price_change.status == PriceChangeStatus.PENDING:
            price_change.status = PriceChangeStatus.REJECTED
            db.commit()
        
        db.close()
        return {"status": "success", "price_change_id": price_change_id}
    
    async def rollback_price_change(self, price_change_id: int) -> Dict:
        """Rollback an applied price change"""
        db = SessionLocal()
        
        try:
            price_change = db.query(PriceChange).filter(
                PriceChange.id == price_change_id
            ).first()
            
            if not price_change or price_change.status != PriceChangeStatus.APPLIED:
                return {"status": "error", "message": "Cannot rollback"}
            
            product = db.query(Product).filter(
                Product.id == price_change.product_id
            ).first()
            
            # Revert to old price
            price_change.final_price = price_change.old_price
            await self._apply_price_change(price_change, product)
            
            price_change.status = PriceChangeStatus.ROLLED_BACK
            db.commit()
            
            return {"status": "success", "price_change_id": price_change_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            db.close()


def get_pricing_engine() -> PricingEngine:
    return PricingEngine()
