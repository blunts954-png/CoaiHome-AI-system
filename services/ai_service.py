"""
AI/LLM Service
Central service for all AI operations: content generation, pricing decisions, product research analysis, support responses.
"""
import json
import openai
from typing import Optional, List, Dict, Any
from datetime import datetime

from config.settings import settings
from models.database import SystemLog, SessionLocal


class AIService:
    """AI Service for dropshipping automation"""
    
    def __init__(self):
        self.provider = settings.ai.provider
        self.api_key = settings.ai.api_key
        self.model = settings.ai.model
        self.temperature = settings.ai.temperature
        self.max_tokens = settings.ai.max_tokens
        
        if self.provider == "openai":
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        else:
            self.client = None
    
    async def _call_llm(self, messages: List[Dict], 
                       tools: Optional[List[Dict]] = None) -> Dict:
        """Call the LLM with messages and optional tools"""
        try:
            if self.provider == "openai":
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
                if tools:
                    kwargs["tools"] = tools
                
                response = await self.client.chat.completions.create(**kwargs)
                return {
                    "content": response.choices[0].message.content,
                    "tool_calls": response.choices[0].message.tool_calls if hasattr(
                        response.choices[0].message, 'tool_calls'
                    ) else None,
                    "raw": response
                }
            
            elif self.provider == "anthropic":
                # Convert OpenAI format to Anthropic format
                system_msg = ""
                user_messages = []
                for msg in messages:
                    if msg["role"] == "system":
                        system_msg = msg["content"]
                    else:
                        user_messages.append(msg)
                
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_msg,
                    messages=user_messages
                )
                return {
                    "content": response.content[0].text,
                    "tool_calls": None,
                    "raw": response
                }
            
            else:
                raise ValueError(f"Unsupported AI provider: {self.provider}")
                
        except Exception as e:
            # Log error
            print(f"AI API Error: {e}")
            raise
    
    def _log_ai_action(self, action_type: str, entity_type: str, entity_id: str,
                      prompt: str, response: str, status: str = "success",
                      extra_data: Optional[Dict] = None):
        """Log AI action to database"""
        try:
            db = SessionLocal()
            log = SystemLog(
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                ai_prompt=prompt[:5000] if prompt else None,  # Truncate if needed
                ai_response=response[:5000] if response else None,
                status=status,
                extra_data=extra_data
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Failed to log AI action: {e}")
    
    # ============ Product Research & Selection ============
    
    async def analyze_product_opportunity(self, product_data: Dict, 
                                         constraints: Dict) -> Dict:
        """
        Analyze if a product is worth importing based on data and constraints
        
        Returns:
            {
                "should_import": bool,
                "confidence": float,
                "reasoning": str,
                "suggested_price": float,
                "suggested_markup": float,
                "risks": List[str],
                "opportunities": List[str]
            }
        """
        prompt = f"""You are an expert dropshipping product researcher. Analyze this product opportunity:

PRODUCT DATA:
{json.dumps(product_data, indent=2)}

BUSINESS CONSTRAINTS:
{json.dumps(constraints, indent=2)}

Your task:
1. Evaluate if this product meets all constraints (margin, shipping time, rating)
2. Assess market demand and competition
3. Suggest optimal pricing (markup multiplier)
4. Identify risks and opportunities

Respond in JSON format:
{{
    "should_import": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation",
    "suggested_price": 0.00,
    "suggested_markup": 0.0,
    "risks": ["risk1", "risk2"],
    "opportunities": ["opp1", "opp2"]
}}
"""
        
        messages = [
            {"role": "system", "content": "You are a dropshipping AI assistant. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            analysis = json.loads(result["content"])
            self._log_ai_action(
                action_type="product_analysis",
                entity_type="product",
                entity_id=product_data.get("id", "unknown"),
                prompt=prompt,
                response=json.dumps(analysis),
                status="success",
                extra_data={"should_import": analysis.get("should_import")}
            )
            return analysis
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            content = result["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            try:
                analysis = json.loads(content.strip())
                return analysis
            except:
                return {
                    "should_import": False,
                    "confidence": 0.0,
                    "reasoning": "Failed to parse AI response",
                    "suggested_price": 0,
                    "suggested_markup": 2.5,
                    "risks": ["AI analysis failed"],
                    "opportunities": []
                }
    
    async def select_best_products(self, products: List[Dict], 
                                   max_selections: int = 5) -> List[Dict]:
        """
        From a list of researched products, select the best ones to import
        
        Returns:
            List of selected products with AI analysis
        """
        prompt = f"""Select the top {max_selections} products to import from this list:

PRODUCTS:
{json.dumps(products, indent=2)}

Criteria:
- Profit margin potential
- Market demand/trending status
- Supplier reliability
- Competition level
- Shipping speed

Return a JSON array of selected product IDs with reasoning:
[
    {{
        "product_id": "id",
        "rank": 1,
        "reasoning": "why this product",
        "confidence": 0.9
    }}
]
"""
        
        messages = [
            {"role": "system", "content": "You are a product selection AI. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            selections = json.loads(result["content"])
            self._log_ai_action(
                action_type="product_selection",
                entity_type="product_list",
                entity_id="batch_selection",
                prompt=prompt,
                response=json.dumps(selections),
                status="success",
                extra_data={"selected_count": len(selections)}
            )
            return selections
        except:
            # Fallback: return empty selection
            return []
    
    # ============ Pricing Optimization ============
    
    async def optimize_prices(self, products: List[Dict], 
                             market_data: Optional[Dict] = None) -> List[Dict]:
        """
        Analyze products and suggest price optimizations
        
        Returns:
            List of price change recommendations
        """
        prompt = f"""You are a pricing optimization AI for dropshipping. Analyze these products and suggest price changes.

PRODUCTS WITH PERFORMANCE DATA:
{json.dumps(products, indent=2)}

MARKET CONTEXT:
{json.dumps(market_data or {}, indent=2)}

CONSTRAINTS:
- Maximum daily price change: {settings.ai.max_price_change_percent}%
- Minimum profit margin: {settings.ai.min_profit_margin}%
- Base markup formula: cost × {settings.store.base_markup}

For each product, decide:
1. Keep current price
2. Increase price (if high demand, low conversion)
3. Decrease price (if low conversion, high views)

Return JSON array:
[
    {{
        "product_id": "id",
        "current_price": 0.00,
        "suggested_price": 0.00,
        "change_percent": 0.0,
        "reasoning": "explanation",
        "confidence": 0.0-1.0,
        "expected_impact": "higher_conversion/higher_margin/etc"
    }}
]
"""
        
        messages = [
            {"role": "system", "content": "You are a pricing AI. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            suggestions = json.loads(result["content"])
            self._log_ai_action(
                action_type="price_optimization",
                entity_type="product_list",
                entity_id="batch_pricing",
                prompt=prompt,
                response=json.dumps(suggestions),
                status="success",
                extra_data={"suggestions_count": len(suggestions)}
            )
            return suggestions
        except:
            return []
    
    # ============ Content Generation ============
    
    async def generate_product_description(self, product_info: Dict, 
                                          brand_tone: str = "professional") -> Dict:
        """Generate SEO-optimized product title and description"""
        prompt = f"""Create compelling, SEO-optimized product copy for this dropshipping product:

PRODUCT INFO:
{json.dumps(product_info, indent=2)}

BRAND TONE: {brand_tone}

Generate:
1. Catchy, SEO-friendly title (max 100 chars)
2. Compelling product description (HTML formatted)
3. 5 bullet points highlighting benefits
4. Meta description (max 160 chars)
5. Recommended tags (5-10 tags)

Return JSON:
{{
    "title": "...",
    "description_html": "...",
    "bullet_points": ["..."],
    "meta_description": "...",
    "tags": ["..."]
}}
"""
        
        messages = [
            {"role": "system", "content": f"You are an expert e-commerce copywriter. Write in a {brand_tone} tone."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            content = json.loads(result["content"])
            self._log_ai_action(
                action_type="content_generation",
                entity_type="product",
                entity_id=product_info.get("id", "unknown"),
                prompt=prompt,
                response=json.dumps(content),
                status="success"
            )
            return content
        except:
            return {
                "title": product_info.get("title", "Product"),
                "description_html": product_info.get("description", ""),
                "bullet_points": [],
                "meta_description": "",
                "tags": []
            }
    
    async def generate_store_content(self, store_spec: Dict) -> Dict:
        """Generate homepage and page content for a new store"""
        prompt = f"""Create compelling store content for this dropshipping store:

STORE SPECIFICATION:
{json.dumps(store_spec, indent=2)}

Generate:
1. Hero section headline and subheadline
2. Value proposition (3-4 bullet points)
3. About Us page content
4. FAQ section (5 common questions)
5. Shipping & Returns policy

Return JSON:
{{
    "hero_headline": "...",
    "hero_subheadline": "...",
    "value_props": ["..."],
    "about_us_html": "...",
    "faq": [{{"q": "...", "a": "..."}}],
    "shipping_policy_html": "..."
}}
"""
        
        messages = [
            {"role": "system", "content": f"You are an expert e-commerce content strategist. Write in a {store_spec.get('brand_tone', 'professional')} tone."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            return json.loads(result["content"])
        except:
            return {}
    
    async def generate_email_template(self, email_type: str, 
                                     context: Dict) -> Dict:
        """Generate email template for various flows"""
        prompt = f"""Create an email for: {email_type}

CONTEXT:
{json.dumps(context, indent=2)}

Generate:
1. Subject line (compelling, not spammy)
2. Email body (HTML)
3. Call-to-action text
4. Preview text

Return JSON:
{{
    "subject": "...",
    "body_html": "...",
    "cta_text": "...",
    "preview_text": "..."
}}
"""
        
        messages = [
            {"role": "system", "content": "You are an email marketing expert. Create conversion-focused emails."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            return json.loads(result["content"])
        except:
            return {}
    
    # ============ Customer Support ============
    
    async def handle_support_ticket(self, ticket_data: Dict, 
                                   policy_context: Dict) -> Dict:
        """
        Generate response to customer support ticket
        
        Returns:
            {
                "can_handle": bool,
                "response": str,
                "confidence": float,
                "requires_approval": bool,
                "category": str,
                "suggested_action": str
            }
        """
        prompt = f"""You are a customer support AI for a dropshipping store. Handle this ticket:

TICKET:
{json.dumps(ticket_data, indent=2)}

STORE POLICIES:
{json.dumps(policy_context, indent=2)}

RULES:
1. Be empathetic and professional
2. Follow store policies exactly
3. For refunds/cancellations over $50, mark as requiring approval
4. For chargebacks/disputes, escalate to human
5. For "Where is my order?", provide tracking info if available

Return JSON:
{{
    "can_handle": true/false,
    "response": "full response text",
    "confidence": 0.0-1.0,
    "requires_approval": true/false,
    "category": "order_status/returns/refund/dispute/general",
    "suggested_action": "send_response/escalate/refund/process_return"
}}
"""
        
        messages = [
            {"role": "system", "content": "You are a helpful customer support AI. Follow policies strictly. Return valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            response_data = json.loads(result["content"])
            self._log_ai_action(
                action_type="support_response",
                entity_type="support_ticket",
                entity_id=ticket_data.get("ticket_id", "unknown"),
                prompt=prompt,
                response=json.dumps(response_data),
                status="success",
                extra_data={"category": response_data.get("category")}
            )
            return response_data
        except:
            return {
                "can_handle": False,
                "response": "Unable to process request",
                "confidence": 0,
                "requires_approval": True,
                "category": "general",
                "suggested_action": "escalate"
            }
    
    # ============ Supplier & Risk Analysis ============
    
    async def analyze_supplier_risk(self, supplier_data: Dict) -> Dict:
        """Analyze supplier performance and suggest actions"""
        prompt = f"""Analyze this supplier's performance data:

SUPPLIER DATA:
{json.dumps(supplier_data, indent=2)}

Provide:
1. Risk assessment (low/medium/high)
2. Recommendation (keep/monitor/replace)
3. Specific concerns
4. Alternative supplier suggestions if needed

Return JSON:
{{
    "risk_level": "low/medium/high",
    "recommendation": "keep/monitor/replace",
    "confidence": 0.0-1.0,
    "concerns": ["..."],
    "action_items": ["..."],
    "alternative_suppliers": ["..."]
}}
"""
        
        messages = [
            {"role": "system", "content": "You are a supplier risk analyst. Return valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        result = await self._call_llm(messages)
        
        try:
            return json.loads(result["content"])
        except:
            return {
                "risk_level": "medium",
                "recommendation": "monitor",
                "confidence": 0.5,
                "concerns": [],
                "action_items": [],
                "alternative_suppliers": []
            }


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
