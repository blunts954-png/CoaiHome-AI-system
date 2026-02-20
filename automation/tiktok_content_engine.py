"""
TikTok Content Automation Engine
Creates viral-worthy content for your Shopify store products
Auto-generates scripts, captions, and content schedules
"""
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

from services.ai_service import get_ai_service
from api_clients.shopify_client import get_shopify_client
from config.settings import settings


class TikTokContentEngine:
    """
    Automated TikTok Content Creation System
    
    Features:
    - Auto-generate video scripts for products
    - Create trending hooks and CTAs
    - Schedule content calendar
    - Generate captions and hashtags
    - Track trending sounds
    """
    
    def __init__(self):
        self.ai = get_ai_service()
        self.shopify = get_shopify_client()
        self.content_calendar = []
        
        # Hook templates that convert
        self.HOOK_TEMPLATES = [
            "POV: You finally found {product_benefit}",
            "Stop scrolling if you hate {pain_point}",
            "This {product_type} saved my {use_case}",
            "I was today years old when I learned about {product_type}",
            "If you have a {target_audience}, you NEED this",
            "This is your sign to get {product_type}",
            "The way this {product_type} changed everything...",
            "TikTok made me buy it and I'm not mad: {product_type}",
            "Things that just make sense: {product_type}",
            "Nobody told me about {product_type} until now",
            "This is the {product_type} your {room_type} needs",
            "If you're still using {old_way}, stop ✋",
            "The {product_type} that broke the internet",
            "I tested {product_type} so you don't have to",
            "This {product_type} went viral for a reason"
        ]
        
        # CTA templates
        self.CTA_TEMPLATES = [
            "Link in bio - only {price}",
            "Get yours now - link in bio!",
            "Shop before it sells out 👆",
            "Double tap if you want this!",
            "Tag someone who needs this",
            "Comment 'LINK' and I'll DM you",
            "Save this for later 💾",
            "Link in bio + use code TIKTOK for 10% off"
        ]
        
        # Content types with optimal timing
        self.CONTENT_TYPES = {
            "product_demo": {
                "duration": "15-30s",
                "best_time": ["12:00", "19:00"],
                "frequency": "daily"
            },
            "before_after": {
                "duration": "10-20s", 
                "best_time": ["8:00", "20:00"],
                "frequency": "3x/week"
            },
            "transformation": {
                "duration": "20-40s",
                "best_time": ["13:00", "21:00"],
                "frequency": "2x/week"
            },
            "tips_educational": {
                "duration": "30-60s",
                "best_time": ["9:00", "15:00"],
                "frequency": "2x/week"
            },
            "asmr_satisfying": {
                "duration": "15-30s",
                "best_time": ["20:00", "22:00"],
                "frequency": "2x/week"
            },
            "storytime": {
                "duration": "45-90s",
                "best_time": ["19:00", "21:00"],
                "frequency": "1x/week"
            }
        }
    
    async def generate_product_script(self, product: Dict, 
                                       content_type: str = "product_demo") -> Dict:
        """
        Generate a viral video script for a product
        
        Args:
            product: Product dict with title, description, price, etc.
            content_type: Type of content to create
        
        Returns:
            Dict with hook, script, cta, hashtags, etc.
        """
        # Extract product info
        title = product.get('title', 'Amazing Product')
        price = product.get('price', '29.99')
        description = product.get('description', '')
        
        # Generate variations based on content type
        if content_type == "product_demo":
            return await self._generate_demo_script(product)
        elif content_type == "before_after":
            return await self._generate_transformation_script(product)
        elif content_type == "problem_solution":
            return await self._generate_problem_solution_script(product)
        elif content_type == "storytime":
            return await self._generate_storytime_script(product)
        else:
            return await self._generate_demo_script(product)
    
    async def _generate_demo_script(self, product: Dict) -> Dict:
        """Generate a product demo script"""
        title = product.get('title', 'Amazing Product')
        price = product.get('price', '$29.99')
        
        # Extract product type from title
        words = title.split()
        product_type = ' '.join(words[:3]) if len(words) > 2 else title
        
        hook = random.choice(self.HOOK_TEMPLATES).format(
            product_benefit=f"the perfect {product_type}",
            pain_point="messy spaces",
            product_type=product_type,
            use_case="morning routine",
            target_audience="small apartment",
            old_way="regular organizers",
            room_type="bedroom"
        )
        
        script = f"""
[0-3s] {hook}
[3-8s] Show the product in use - highlight key feature
[8-15s] Show result/benefit
[15-20s] Show different use cases
[20-25s] Price reveal with shock face
[25-30s] CTA
        """.strip()
        
        return {
            "hook": hook,
            "script": script,
            "cta": f"Link in bio - only {price}",
            "duration": "30s",
            "hashtags": self._generate_hashtags(product),
            "caption": self._generate_caption(product),
            "text_overlay": [
                "Wait for it...",
                "This is genius",
                f"Only {price}",
                "Link in bio 🔗"
            ]
        }
    
    async def _generate_transformation_script(self, product: Dict) -> Dict:
        """Generate before/after transformation script"""
        title = product.get('title', 'Product')
        
        hook = f"The before and after will shock you 😱"
        
        script = f"""
[0-3s] {hook}
[3-5s] Show messy/problem state
[5-8s] Add {title} 
[8-12s] Quick transformation montage
[12-15s] Reveal organized/beautiful result
[15-20s] Your reaction + CTA
        """.strip()
        
        return {
            "hook": hook,
            "script": script,
            "cta": "Get organized - link in bio!",
            "duration": "20s",
            "hashtags": ["#beforeandafter", "#transformation", "#organization", "#satisfying"],
            "caption": f"POV: You discovered the {title} ✨\n\nLink in bio to transform your space!",
            "text_overlay": ["Before 😫", "After ✨", "Game changer!"]
        }
    
    async def _generate_problem_solution_script(self, product: Dict) -> Dict:
        """Generate problem/solution format script"""
        title = product.get('title', 'This product')
        
        hook = "Stop doing this 👇"
        
        script = f""
[0-3s] {hook} + show the frustrating old way
[3-8s] Problem demonstration
[8-12s] "Instead, try this:" + reveal product
[12-18s] Show it solving the problem
[18-25s] Multiple use cases
[25-30s] CTA
        """.strip()
        
        return {
            "hook": hook,
            "script": script,
            "cta": random.choice(self.CTA_TEMPLATES),
            "duration": "30s",
            "hashtags": ["#lifehack", "#tiktokmademebuyit", "#amazonfinds", "#musthave"],
            "caption": f"Why didn't I find this sooner?! 🤯\n\n{title} - link in bio!",
            "text_overlay": ["Stop ❌", "Start ✅", "Link in bio 🔗"]
        }
    
    async def _generate_storytime_script(self, product: Dict) -> Dict:
        """Generate storytime format script"""
        title = product.get('title', 'This item')
        
        hook = "Storytime: how this changed my life"
        
        script = f"""
[0-5s] {hook}
[5-15s] Tell relatable story about the problem
[15-30s] Discovery moment
[30-45s] Using the product
[45-60s] Results + recommendation
[60-75s] CTA + personal endorsement
        """.strip()
        
        return {
            "hook": hook,
            "script": script,
            "cta": "Link in bio - game changer!",
            "duration": "75s",
            "hashtags": ["#storytime", "#review", "#honestreview", "#worthit"],
            "caption": f"Real talk about {title}\n\nSpoiler: 10/10 recommend ⭐\nLink in bio!",
            "text_overlay": ["Storytime 📖", "Part 1"]
        }
    
    def _generate_hashtags(self, product: Dict) -> List[str]:
        """Generate relevant hashtags for product"""
        title = product.get('title', '').lower()
        
        # Base hashtags
        base = ["#tiktokmademebuyit", "#amazonfinds", "#musthave"]
        
        # Category hashtags
        categories = {
            "kitchen": ["#kitchenhacks", "#kitchenorganization", "#cookinghacks"],
            "bathroom": ["#bathroomorganization", "#bathroomdecor", "#selfcare"],
            "bedroom": ["#bedroomdecor", "#roommakeover", "#homedecor"],
            "office": ["#desksetup", "#officedecor", "#workfromhome"],
            "car": ["#caraccessories", "#cargadgets", "#carhacks"],
            "beauty": ["#beautyhacks", "#skincare", "#makeup"],
            "pet": ["#petsoftiktok", "#dogtok", "#cattok"],
            "organization": ["#organization", "#homeorganization", "#declutter"],
            "gadget": ["#gadgets", "#techtok", "#coolgadgets"]
        }
        
        matched = []
        for cat, tags in categories.items():
            if cat in title or any(word in title for word in cat.split()):
                matched.extend(tags)
        
        return base + matched[:5]  # Max 8 hashtags
    
    def _generate_caption(self, product: Dict) -> str:
        """Generate engaging caption"""
        title = product.get('title', 'This product')
        price = product.get('price', '')
        
        templates = [
            f"POV: You found the perfect {title} 🥹\n\nLink in bio!",
            f"This {title} went viral for a reason 🔥\n\nGet yours - link in bio!",
            f"Why didn't anyone tell me about {title} sooner?! 🤯\n\nLink in bio + use code TIKTOK10",
            f"The way this changed everything... ✨\n\n{title} - link in bio!",
            f"Add to cart energy 🛒✨\n\n{title}\nLink in bio!"
        ]
        
        return random.choice(templates)
    
    async def create_30_day_calendar(self, products: List[Dict]) -> List[Dict]:
        """
        Create a 30-day content calendar
        
        Args:
            products: List of products to create content for
        
        Returns:
            List of content items with dates, scripts, etc.
        """
        calendar = []
        start_date = datetime.now()
        
        content_types = list(self.CONTENT_TYPES.keys())
        
        for day in range(30):
            date = start_date + timedelta(days=day)
            
            # 2-3 posts per day
            posts_per_day = 2 if day % 3 != 0 else 3  # Extra post every 3rd day
            
            for post_num in range(posts_per_day):
                # Rotate through products
                product = products[day % len(products)] if products else None
                
                # Rotate content types
                content_type = content_types[day % len(content_types)]
                
                # Generate script
                if product:
                    content = await self.generate_product_script(product, content_type)
                else:
                    content = await self._generate_generic_content(content_type)
                
                # Calculate post time
                best_times = self.CONTENT_TYPES[content_type]["best_time"]
                post_time = best_times[post_num % len(best_times)]
                
                calendar.append({
                    "day": day + 1,
                    "date": date.strftime("%Y-%m-%d"),
                    "post_time": post_time,
                    "content_type": content_type,
                    "product": product.get('title') if product else None,
                    "hook": content["hook"],
                    "script": content["script"],
                    "cta": content["cta"],
                    "hashtags": content["hashtags"],
                    "caption": content["caption"],
                    "text_overlay": content.get("text_overlay", []),
                    "status": "scheduled"
                })
        
        self.content_calendar = calendar
        return calendar
    
    async def _generate_generic_content(self, content_type: str) -> Dict:
        """Generate generic content when no product specified"""
        generic_hooks = {
            "tips_educational": "5 organization mistakes you're making",
            "asmr_satisfying": "Satisfying organization ASMR",
            "storytime": "How I organize my entire home in 1 hour"
        }
        
        hook = generic_hooks.get(content_type, "Organization tips you need 🏠")
        
        return {
            "hook": hook,
            "script": "Educational content script",
            "cta": "Follow for daily tips!",
            "hashtags": ["#homeorganization", "#organizationtips", "#cleanhome"],
            "caption": hook + "\n\nFollow for more! ✨",
            "text_overlay": ["Tip 1", "Tip 2", "Tip 3"]
        }
    
    async def get_trending_sounds(self) -> List[Dict]:
        """
        Get currently trending sounds on TikTok
        Note: This would integrate with TikTok API or scraping
        """
        # Placeholder - in production would scrape or use API
        return [
            {"name": "Original Sound - Creator", "trending": True, "category": "viral"},
            {"name": "Trending Audio 2024", "trending": True, "category": "music"},
            {"name": "Satisfying Sounds", "trending": True, "category": "asmr"}
        ]
    
    def export_calendar_to_csv(self, filename: str = "content_calendar.csv"):
        """Export calendar to CSV for easy viewing"""
        import csv
        
        if not self.content_calendar:
            print("No calendar to export. Run create_30_day_calendar first.")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'day', 'date', 'post_time', 'content_type', 'product',
                'hook', 'script', 'cta', 'hashtags', 'caption', 'status'
            ])
            writer.writeheader()
            for item in self.content_calendar:
                # Convert lists to strings for CSV
                row = item.copy()
                row['hashtags'] = ' '.join(row['hashtags']) if isinstance(row['hashtags'], list) else row['hashtags']
                row['text_overlay'] = '|'.join(row['text_overlay']) if isinstance(row['text_overlay'], list) else ''
                writer.writerow(row)
        
        print(f"✅ Calendar exported to {filename}")
    
    async def auto_create_content_for_store(self, store_products: Optional[List[Dict]] = None) -> Dict:
        """
        Automatically create content for all store products
        
        Args:
            store_products: List of products (if None, fetches from Shopify)
        
        Returns:
            Dict with calendar and summary
        """
        if store_products is None:
            # Fetch from Shopify
            products_result = await self.shopify.list_products(limit=50)
            products = products_result.get('products', [])
            store_products = [
                {
                    'title': p.get('title'),
                    'price': p.get('variants', [{}])[0].get('price', '29.99'),
                    'description': p.get('body_html', ''),
                    'id': p.get('id')
                }
                for p in products
            ]
        
        print(f"🎬 Creating content for {len(store_products)} products...")
        
        # Create calendar
        calendar = await self.create_30_day_calendar(store_products)
        
        # Export
        self.export_calendar_to_csv()
        
        return {
            "products": len(store_products),
            "content_pieces": len(calendar),
            "calendar": calendar[:5],  # First 5 items
            "export_file": "content_calendar.csv",
            "message": "30-day content calendar created!"
        }


# Singleton
_content_engine: Optional[TikTokContentEngine] = None


def get_tiktok_content_engine() -> TikTokContentEngine:
    """Get or create content engine"""
    global _content_engine
    if _content_engine is None:
        _content_engine = TikTokContentEngine()
    return _content_engine
