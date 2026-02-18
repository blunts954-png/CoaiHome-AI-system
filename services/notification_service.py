"""
Notification Service
Handles email and Slack notifications for the automation system
"""
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime

from config.settings import settings


class NotificationService:
    """Handles all system notifications"""
    
    def __init__(self):
        self.config = settings.notifications
    
    async def send_email(self, subject: str, body: str, 
                        to_email: Optional[str] = None) -> bool:
        """Send an email notification"""
        if not self.config.email_enabled:
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_user
            msg["To"] = to_email or self.config.alert_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(body, "html"))
            
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_user, self.config.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    async def send_slack(self, message: str, blocks: Optional[List[Dict]] = None) -> bool:
        """Send a Slack notification"""
        if not self.config.slack_enabled:
            return False
        
        try:
            payload = {"text": message}
            if blocks:
                payload["blocks"] = blocks
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.slack_webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Failed to send Slack message: {e}")
            return False
    
    async def send_exception_summary(self, total: int, auto_resolved: int):
        """Send daily exception summary"""
        subject = f"🚨 Dropshipping AI - {total} New Exceptions"
        
        body = f"""
        <h2>Order Fulfillment Exception Report</h2>
        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <ul>
            <li>Total Exceptions: {total}</li>
            <li>Auto-Resolved: {auto_resolved}</li>
            <li>Requires Attention: {total - auto_resolved}</li>
        </ul>
        <p>View the exception queue in your dashboard to take action.</p>
        """
        
        await self.send_email(subject, body)
        
        # Also send to Slack
        slack_msg = f"🚨 *Exception Alert*: {total} new fulfillment exceptions ({auto_resolved} auto-resolved)"
        await self.send_slack(slack_msg)
    
    async def send_supplier_alert(self, concerning_suppliers: List[Dict]):
        """Send alert about concerning suppliers"""
        subject = f"⚠️ Supplier Performance Alert - {len(concerning_suppliers)} Suppliers Need Attention"
        
        supplier_list = "\n".join([
            f"<li>{s['name']} (Score: {s['score']:.1f}) - {s['recommendation']}</li>"
            for s in concerning_suppliers
        ])
        
        body = f"""
        <h2>Supplier Performance Alert</h2>
        <p>The following suppliers have been flagged by the AI:</p>
        <ul>
            {supplier_list}
        </ul>
        <p>Consider switching suppliers for products using these vendors.</p>
        """
        
        await self.send_email(subject, body)
    
    async def send_daily_summary(self, stats: Dict):
        """Send daily operations summary"""
        if not self.config.daily_summary_enabled:
            return
        
        subject = f"📊 Daily Dropshipping Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        <h2>Daily Operations Summary</h2>
        <h3>Products</h3>
        <ul>
            <li>New Products Researched: {stats.get('products_researched', 0)}</li>
            <li>Products Imported: {stats.get('products_imported', 0)}</li>
            <li>Price Changes: {stats.get('price_changes', 0)}</li>
        </ul>
        
        <h3>Orders</h3>
        <ul>
            <li>New Orders: {stats.get('new_orders', 0)}</li>
            <li>Exceptions: {stats.get('exceptions', 0)}</li>
        </ul>
        
        <h3>Revenue</h3>
        <ul>
            <li>Total Revenue: ${stats.get('revenue', 0):.2f}</li>
            <li>Profit: ${stats.get('profit', 0):.2f}</li>
        </ul>
        """
        
        await self.send_email(subject, body)
        
        # Slack summary
        slack_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Products Imported*\n{stats.get('products_imported', 0)}"},
                    {"type": "mrkdwn", "text": f"*Price Changes*\n{stats.get('price_changes', 0)}"},
                    {"type": "mrkdwn", "text": f"*New Orders*\n{stats.get('new_orders', 0)}"},
                    {"type": "mrkdwn", "text": f"*Exceptions*\n{stats.get('exceptions', 0)}"},
                ]
            }
        ]
        
        await self.send_slack("Daily Summary", slack_blocks)


# Singleton
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
