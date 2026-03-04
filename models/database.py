"""
SQLAlchemy models for the dropshipping automation system.
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, Text, JSON, ForeignKey, Enum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

from config.settings import settings

# Handle Railway's DATABASE_URL format
# Railway uses postgres:// but SQLAlchemy needs postgresql://
db_url = settings.system.database_url

# Clean up URL (remove quotes, brackets, whitespace)
if isinstance(db_url, str):
    db_url = db_url.strip(' "\'')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Check for un-interpolated Railway templates
    if "${{" in db_url:
        print("⚠️  Warning: DATABASE_URL contains a template placeholder. Falling back to SQLite.")
        db_url = "sqlite:///./dropshipping_ai.db"

# Create database directory if it doesn't exist (for SQLite)
if "sqlite" in db_url:
    db_path = db_url.replace("sqlite:///", "")
    # Handle both Unix and Windows paths
    db_path = db_path.replace("\\", "/")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

Base = declarative_base()

try:
    engine = create_engine(
        db_url, 
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        pool_pre_ping=True  # Check connection before using (helps with Railway)
    )
    # Test connection
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"❌ Error: Could not connect to database with URL: {db_url}")
    print(f"Details: {e}")
    print("⚠️  Falling back to local SQLite database...")
    db_url = "sqlite:///./dropshipping_ai.db"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    PAUSED = "paused"
    OUT_OF_STOCK = "out_of_stock"
    REMOVED = "removed"


class PriceChangeStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"


class Store(Base):
    """Stores created via AI Store Builder"""
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True)
    shopify_store_id = Column(String(255), unique=True, index=True)
    shopify_domain = Column(String(255), unique=True, index=True)
    brand_name = Column(String(255))
    niche = Column(String(255))
    target_country = Column(String(10), default="US")
    currency = Column(String(10), default="USD")
    
    # Branding
    primary_color = Column(String(50))
    secondary_color = Column(String(50))
    brand_tone = Column(String(50))
    logo_url = Column(Text)
    
    # Settings
    autods_connected = Column(Boolean, default=False)
    auto_fulfillment_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="store")


class Product(Base):
    """Products in the catalog"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), index=True)
    
    # Shopify data
    shopify_product_id = Column(String(255), index=True)
    shopify_variant_id = Column(String(255))
    
    # AutoDS data
    autods_product_id = Column(String(255), index=True)
    supplier_id = Column(String(255))
    supplier_name = Column(String(255))
    
    # Product info
    title = Column(String(500))
    description = Column(Text)
    sku = Column(String(255), index=True)
    
    # Pricing
    cost_price = Column(Float, default=0.0)
    selling_price = Column(Float, default=0.0)
    suggested_price = Column(Float, default=0.0)
    min_price = Column(Float, default=0.0)
    markup_multiplier = Column(Float, default=2.5)
    profit_margin_percent = Column(Float, default=0.0)
    
    # Status
    status = Column(Enum(ProductStatus), default=ProductStatus.DRAFT)
    
    # Supplier data
    supplier_rating = Column(Float)
    shipping_days = Column(Integer)
    stock_quantity = Column(Integer, default=0)
    
    # Performance metrics
    views = Column(Integer, default=0)
    add_to_carts = Column(Integer, default=0)
    orders = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    refund_rate = Column(Float, default=0.0)
    
    # AI metadata
    ai_import_confidence = Column(Float)
    ai_research_data = Column(JSON)
    tags = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced_at = Column(DateTime)
    
    # Relationships
    store = relationship("Store", back_populates="products")
    price_changes = relationship("PriceChange", back_populates="product")


class PriceChange(Base):
    """Track AI-suggested and applied price changes"""
    __tablename__ = "price_changes"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    
    old_price = Column(Float)
    suggested_price = Column(Float)
    final_price = Column(Float)
    
    # AI reasoning
    ai_reasoning = Column(Text)
    confidence_score = Column(Float)
    
    # Market data used for decision
    competitor_price = Column(Float)
    demand_score = Column(Float)
    conversion_rate = Column(Float)
    
    # Status
    status = Column(Enum(PriceChangeStatus), default=PriceChangeStatus.PENDING)
    approved_by = Column(String(255))
    approved_at = Column(DateTime)
    applied_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="price_changes")


class ProductResearchJob(Base):
    """Track product research and import jobs"""
    __tablename__ = "product_research_jobs"
    
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), index=True)
    
    # Search criteria
    niche = Column(String(255))
    min_margin = Column(Float)
    max_shipping_days = Column(Integer)
    min_rating = Column(Float)
    
    # Results
    products_found = Column(Integer, default=0)
    products_selected = Column(Integer, default=0)
    products_imported = Column(Integer, default=0)
    
    # Raw research data
    research_data = Column(JSON)
    
    # Status
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class OrderException(Base):
    """Track orders that failed auto-fulfillment"""
    __tablename__ = "order_exceptions"
    
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), index=True)
    
    shopify_order_id = Column(String(255), index=True)
    autods_order_id = Column(String(255))
    
    exception_type = Column(String(100))  # stock_out, payment_failed, supplier_issue, etc.
    error_message = Column(Text)
    
    # Order details
    customer_email = Column(String(255))
    total_amount = Column(Float)
    product_ids = Column(JSON)
    
    # Resolution
    status = Column(String(50), default="open")  # open, resolved, escalated
    resolution_notes = Column(Text)
    resolved_by = Column(String(255))
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SupplierPerformance(Base):
    """Track supplier metrics for AI supplier switching decisions"""
    __tablename__ = "supplier_performance"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(String(255), index=True)
    supplier_name = Column(String(255))
    
    # Metrics
    total_orders = Column(Integer, default=0)
    successful_fulfillments = Column(Integer, default=0)
    failed_fulfillments = Column(Integer, default=0)
    avg_fulfillment_days = Column(Float, default=0.0)
    refund_rate = Column(Float, default=0.0)
    stockout_count = Column(Integer, default=0)
    
    # AI scoring
    reliability_score = Column(Float, default=0.0)
    ai_recommendation = Column(String(50))  # keep, monitor, replace
    
    last_updated = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    """Audit log for all AI actions"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    action_type = Column(String(100), index=True)  # price_change, product_import, etc.
    entity_type = Column(String(100))  # product, order, store
    entity_id = Column(String(255))
    
    # AI decision data
    ai_prompt = Column(Text)
    ai_response = Column(Text)
    
    # Action result
    status = Column(String(50))  # success, failed, pending
    error_message = Column(Text)
    extra_data = Column(JSON)  # Was 'metadata' - reserved by SQLAlchemy
    
    user_override = Column(Boolean, default=False)
    override_by = Column(String(255))


class CustomerSupportTicket(Base):
    """AI-handled support tickets"""
    __tablename__ = "customer_support_tickets"
    
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(255), unique=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    
    # Customer info
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    shopify_customer_id = Column(String(255))
    
    # Ticket content
    subject = Column(String(500))
    message = Column(Text)
    category = Column(String(100))  # order_status, return, general, etc.
    
    # AI handling
    ai_classification = Column(String(100))
    ai_response_draft = Column(Text)
    ai_confidence = Column(Float)
    
    # Related data
    related_order_id = Column(String(255))
    tracking_number = Column(String(255))
    
    # Status
    status = Column(String(50), default="ai_handling")  # ai_handling, human_review, resolved
    requires_approval = Column(Boolean, default=False)
    approved_response = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


class OrderStatus(str, enum.Enum):
    RECEIVED = "received"
    PAID = "paid"
    ON_HOLD = "on_hold"
    SENT_TO_CJ = "sent_to_cj"
    TRACKING_UPDATED = "tracking_updated"
    FAILED = "failed"


class TikTokOrderStatus(str, enum.Enum):
    UNPAID = "unpaid"
    AWAITING_SHIPMENT = "awaiting_shipment"
    AWAITING_COLLECTION = "awaiting_collection"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"



class ShopifyOrder(Base):
    """Tracks the end-to-end fulfillment of a Shopify order via CJ."""
    __tablename__ = "shopify_orders"
    
    id = Column(Integer, primary_key=True)
    shopify_order_id = Column(String(255), unique=True, index=True, nullable=False)
    order_name = Column(String(100), nullable=True)  # e.g. "#1001"
    customer_email = Column(String(255), nullable=True)
    total_price = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)

    status = Column(Enum(OrderStatus), default=OrderStatus.RECEIVED, nullable=False)
    cj_order_id = Column(String(255), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    logistics_company = Column(String(255), nullable=True)
    last_error = Column(Text, default="")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VariantMap(Base):
    """
    Backwards compatibility: Links Shopify variants to CJ supplier variants.
    """
    __tablename__ = "variant_map"
    
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), index=True)
    shopify_variant_id = Column(String(255), unique=True, index=True, nullable=False)
    cj_variant_id = Column(String(255), index=True, nullable=False)
    sku = Column(String(255))
    active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalVariantMapping(Base):
    """
    The 'Nervous System' core: Polyglot mapping for multi-channel sync.
    """
    __tablename__ = "global_variant_mappings"

    id = Column(Integer, primary_key=True)
    master_sku = Column(String(255), unique=True, index=True)
    
    # CJ (The Source)
    cj_product_id = Column(String(255), index=True)
    cj_variant_id = Column(String(255), index=True)
    
    # Shopify
    shopify_product_id = Column(String(255), index=True)
    shopify_variant_id = Column(String(255), index=True)
    
    # TikTok Shop
    tt_shop_product_id = Column(String(255), index=True)
    tt_shop_variant_id = Column(String(255), index=True)
    
    # Status & Buffers
    active = Column(Boolean, default=True)
    inventory_buffer = Column(Integer, default=5) # Prevent overselling
    last_known_inventory = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TikTokShopOrder(Base):
    """Tracks orders coming from TikTok Shop directly."""
    __tablename__ = "tiktok_shop_orders"

    id = Column(Integer, primary_key=True)
    tt_order_id = Column(String(255), unique=True, index=True, nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"))
    
    status = Column(Enum(TikTokOrderStatus), default=TikTokOrderStatus.AWAITING_SHIPMENT)
    cj_order_id = Column(String(255), nullable=True) # Linked CJ order
    
    total_amount = Column(Float)
    customer_name = Column(String(255))
    
    tracking_number = Column(String(255), nullable=True)
    ship_by_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class ShopifyOAuthState(Base):
    """Persist OAuth state values to survive process restarts."""
    __tablename__ = "shopify_oauth_states"

    id = Column(Integer, primary_key=True)
    state = Column(String(255), unique=True, index=True, nullable=False)
    shop = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    consumed_at = Column(DateTime)


class ShopifyInstallation(Base):
    """Persist installed Shopify shop tokens across deploys/workers."""
    __tablename__ = "shopify_installations"

    id = Column(Integer, primary_key=True)
    shop = Column(String(255), unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)
    scope = Column(Text, default="")
    installed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
