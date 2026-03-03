"""
Central configuration for the AI Dropshipping Automation System.
All settings are loaded from environment variables with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import Optional, List, Any
from functools import lru_cache
from dotenv import load_dotenv

# Explicitly load .env file before defining settings
load_dotenv(override=True)


class ShopifyConfig(BaseSettings):
    """Shopify API Configuration"""
    model_config = SettingsConfigDict(env_prefix="SHOPIFY_")
    
    shop_url: str = Field(default="", description="Shopify store URL (e.g., mystore.myshopify.com)")
    api_key: str = Field(default="", description="Shopify App Client ID (for OAuth)")
    api_secret: str = Field(default="", description="Shopify App Secret (for OAuth)")
    access_token: str = Field(default="", description="Shopify Admin API access token (for direct API calls)")
    api_version: str = Field(default="2024-01", description="Shopify API version")
    webhook_secret: str = Field(default="", description="Webhook validation secret")
    app_url: str = Field(default="", description="Public app URL (e.g., https://your-app.up.railway.app)")
    ssl_verify: bool = Field(default=True, description="Verify TLS certificates for Shopify HTTPS requests")
    api_scopes: str = Field(
        default="read_products,write_products,read_orders,write_orders,read_inventory,write_inventory,read_customers",
        description="Comma-separated Shopify OAuth scopes"
    )


class AutoDSConfig(BaseSettings):
    """AutoDS API Configuration"""
    model_config = SettingsConfigDict(env_prefix="AUTODS_")
    
    api_key: str = Field(default="", description="AutoDS API key")
    base_url: str = Field(default="https://api.autods.com", description="AutoDS API base URL")
    webhook_secret: str = Field(default="", description="Webhook secret for validation")
    
    # AutoDS Feature Toggles
    auto_fulfillment_enabled: bool = Field(default=True, description="Enable auto-fulfillment")
    auto_pricing_enabled: bool = Field(default=True, description="Enable AI pricing optimization")
    auto_import_enabled: bool = Field(default=True, description="Enable auto product import")


class CJConfig(BaseSettings):
    """CJ Dropshipping API Configuration"""
    model_config = SettingsConfigDict(env_prefix="CJ_")

    api_token: str = Field(default="", description="CJ API token (full token from CJ)")
    api_email: str = Field(default="", description="CJ API email (before @api@)")
    api_key: str = Field(default="", description="CJ API key (after @api@)")
    base_url: str = Field(
        default="https://developers.cjdropshipping.com/api2.0/v1",
        description="CJ API base URL"
    )
    default_country: str = Field(default="US", description="Default shipping country")
    auto_import_enabled: bool = Field(default=True, description="Enable auto product import from CJ")
    auto_fulfillment_enabled: bool = Field(default=True, description="Enable order handling via CJ APIs")


class AIConfig(BaseSettings):
    """AI/LLM Configuration"""
    model_config = SettingsConfigDict(env_prefix="AI_")
    
    provider: str = Field(default="openai", description="AI provider: openai, anthropic, or local")
    api_key: str = Field(default="", description="AI provider API key")
    model: str = Field(default="gpt-4-turbo-preview", description="Model to use")
    temperature: float = Field(default=0.3, description="Temperature for AI responses")
    max_tokens: int = Field(default=2000, description="Max tokens per response")
    
    # Business Guardrails
    max_price_change_percent: float = Field(default=10.0, description="Max daily price change %")
    min_profit_margin: float = Field(default=30.0, description="Minimum profit margin %")
    max_products_per_day: int = Field(default=5, description="Max new products to import daily")
    min_product_rating: float = Field(default=4.0, description="Minimum supplier rating")
    max_shipping_days: int = Field(default=14, description="Maximum shipping time in days")


class StoreConfig(BaseSettings):
    """Store Branding and Business Rules"""
    model_config = SettingsConfigDict(env_prefix="STORE_")
    
    niche: str = Field(default="", description="Store niche/category")
    brand_name: str = Field(default="", description="Store brand name")
    target_country: str = Field(default="US", description="Primary market")
    currency: str = Field(default="USD", description="Store currency")
    
    # Branding
    primary_color: str = Field(default="#000000", description="Primary brand color")
    secondary_color: str = Field(default="#ffffff", description="Secondary brand color")
    brand_tone: str = Field(default="professional", description="Brand voice: professional, casual, luxury, etc.")
    
    # Pricing Rules
    base_markup: float = Field(default=2.5, description="Base price multiplier")
    min_price: float = Field(default=15.0, description="Minimum product price")
    max_price: float = Field(default=500.0, description="Maximum product price")
    price_rounding: float = Field(default=0.99, description="Price rounding (e.g., 0.99)")


class NotificationConfig(BaseSettings):
    """Notification and Alert Configuration"""
    model_config = SettingsConfigDict(env_prefix="NOTIFY_")
    
    email_enabled: bool = Field(default=False)
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    alert_email: str = Field(default="")
    
    slack_enabled: bool = Field(default=False)
    slack_webhook_url: str = Field(default="")
    
    daily_summary_enabled: bool = Field(default=True)


class SystemConfig(BaseSettings):
    """System-wide Configuration"""
    model_config = SettingsConfigDict(env_prefix="SYSTEM_")
    
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    # Use Railway's DATABASE_URL if available, fallback to SQLite
    database_url: str = Field(default="sqlite:///./dropshipping_ai.db", description="Database connection URL")
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # CORS - comma-separated list of allowed origins (e.g., "https://domain1.com,https://domain2.com")
    # Leave empty or unset to allow all origins (development mode)
    cors_allowed_origins: str = Field(default="", description="Comma-separated allowed CORS origins")
    
    # Automation Schedules
    pricing_check_interval_hours: int = Field(default=24)
    inventory_check_interval_minutes: int = Field(default=30)
    product_research_interval_hours: int = Field(default=24)
    
    # Approval Gates
    require_approval_for_import: bool = Field(default=False)
    require_approval_for_price_changes: bool = Field(default=False)
    require_approval_for_refunds: bool = Field(default=True, description="Always require approval for refunds")
    supplier_platform: str = Field(
        default="cj",
        description="Supplier platform: cj (recommended), or autods"
    )


class Settings(BaseSettings):
    """Main settings container"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    shopify: ShopifyConfig = Field(default_factory=ShopifyConfig)
    autods: AutoDSConfig = Field(default_factory=AutoDSConfig)
    cj: CJConfig = Field(default_factory=CJConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    store: StoreConfig = Field(default_factory=StoreConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    
    @model_validator(mode='after')
    def validate_env_overrides(cls, self) -> 'Settings':
        """Ensure environment variables override defaults after Pydantic loads."""
        # Override ssl_verify from env (SHOPIFY_SSL_VERIFY)
        ssl_verify_env = os.getenv("SHOPIFY_SSL_VERIFY")
        if ssl_verify_env is not None:
            self.shopify.ssl_verify = ssl_verify_env.lower() == "true"
        
        # Override database_url from env (DATABASE_URL)
        db_url_env = os.getenv("DATABASE_URL")
        if db_url_env is not None:
            self.system.database_url = db_url_env
        
        return self


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export for easy import
settings = get_settings()
