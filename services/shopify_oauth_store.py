"""Database-backed storage for Shopify OAuth flow."""
from datetime import datetime, timedelta
from typing import Optional

from models.database import SessionLocal, ShopifyInstallation, ShopifyOAuthState


OAUTH_STATE_TTL_MINUTES = 15


def save_oauth_state(state: str, shop: str) -> None:
    db = SessionLocal()
    try:
        row = ShopifyOAuthState(state=state, shop=shop)
        db.add(row)
        db.commit()
    finally:
        db.close()


def consume_oauth_state(state: str, shop: str) -> bool:
    db = SessionLocal()
    try:
        row = db.query(ShopifyOAuthState).filter(ShopifyOAuthState.state == state).first()
        if not row:
            return False

        if row.shop != shop or row.consumed_at is not None:
            return False

        too_old = datetime.utcnow() - timedelta(minutes=OAUTH_STATE_TTL_MINUTES)
        if row.created_at < too_old:
            return False

        row.consumed_at = datetime.utcnow()
        db.commit()
        return True
    finally:
        db.close()


def upsert_installation(shop: str, access_token: str, scope: str = "") -> None:
    db = SessionLocal()
    try:
        row = db.query(ShopifyInstallation).filter(ShopifyInstallation.shop == shop).first()
        if row:
            row.access_token = access_token
            row.scope = scope
            row.updated_at = datetime.utcnow()
        else:
            row = ShopifyInstallation(shop=shop, access_token=access_token, scope=scope)
            db.add(row)
        db.commit()
    finally:
        db.close()


def get_installation(shop: str) -> Optional[ShopifyInstallation]:
    db = SessionLocal()
    try:
        row = db.query(ShopifyInstallation).filter(ShopifyInstallation.shop == shop).first()
        if not row:
            return None
        db.expunge(row)
        return row
    finally:
        db.close()


def get_any_installation() -> Optional[ShopifyInstallation]:
    db = SessionLocal()
    try:
        row = db.query(ShopifyInstallation).order_by(ShopifyInstallation.updated_at.desc()).first()
        if not row:
            return None
        db.expunge(row)
        return row
    finally:
        db.close()
